import ccxt
import pandas as pd
from typing import Dict

# freqtrade imports - available after installing freqtrade
try:
    from freqtrade.strategy.interface import IStrategy
    import talib.abstract as ta
except ImportError:  # pragma: no cover - optional dependency
    # Fallback when freqtrade or TA-Lib are not installed.
    IStrategy = object
    ta = None

# Simple EMA/RSI implementations if TA-Lib is missing
def _ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential moving average calculated with pandas."""
    return series.ewm(span=period, adjust=False).mean()


def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index using pandas operations."""
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    ma_up = up.ewm(com=period - 1, adjust=False).mean()
    ma_down = down.ewm(com=period - 1, adjust=False).mean()
    rs = ma_up / ma_down
    return 100 - (100 / (1 + rs))


class AdvancedStrategy(IStrategy):
    """Example strategy with EMA crossover and RSI filter."""

    timeframe = '5m'
    minimal_roi = {"0": 0.03}
    stoploss = -0.1

    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.015

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        """Add EMA and RSI columns using TA-Lib or pandas fallbacks."""
        if ta is not None:
            dataframe['ema_fast'] = ta.EMA(dataframe['close'], timeperiod=12)
            dataframe['ema_slow'] = ta.EMA(dataframe['close'], timeperiod=26)
            dataframe['rsi'] = ta.RSI(dataframe['close'], timeperiod=14)
        else:
            dataframe['ema_fast'] = _ema(dataframe['close'], 12)
            dataframe['ema_slow'] = _ema(dataframe['close'], 26)
            dataframe['rsi'] = _rsi(dataframe['close'], 14)
        return dataframe

    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['ema_fast'] > dataframe['ema_slow']) &
                (dataframe['rsi'] < 70)
            ),
            'enter_long'
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['ema_fast'] < dataframe['ema_slow']) |
                (dataframe['rsi'] > 80)
            ),
            'exit_long'
        ] = 1
        return dataframe

def fetch_candles(exchange, symbol, timeframe='5m', limit=100):
    ohlc = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlc, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df


def calculate_position_size(balance, risk_percent, price, stop_distance):
    risk_amount = balance * risk_percent
    quantity = risk_amount / (stop_distance * price)
    return max(quantity, 0)


def main():
    exchange = ccxt.binance({'enableRateLimit': True})
    symbol = 'BTC/USDT'
    dataframe = fetch_candles(exchange, symbol)

    strategy = AdvancedStrategy()
    dataframe = strategy.populate_indicators(dataframe, metadata={})
    dataframe = strategy.populate_entry_trend(dataframe, metadata={})
    dataframe = strategy.populate_exit_trend(dataframe, metadata={})

    last = dataframe.iloc[-1]
    balance = exchange.fetch_balance()['free'].get('USDT', 0)
    price = last['close']

    if last.get('enter_long'):
        stop_distance = price * abs(strategy.stoploss)
        amount = calculate_position_size(balance, 0.01, price, stop_distance)
        print(f"Buy signal. Would place order for {amount:.6f} {symbol} at {price}")
    elif last.get('exit_long'):
        print("Sell signal. Would exit position.")
    else:
        print("No trade signal.")


if __name__ == '__main__':
    main()
