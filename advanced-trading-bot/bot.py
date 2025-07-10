import ccxt
import pandas as pd
from typing import Dict

# freqtrade imports - available after installing freqtrade
try:
    from freqtrade.strategy.interface import IStrategy
    import talib.abstract as ta
except ImportError:
    IStrategy = object
    ta = None


class AdvancedStrategy(IStrategy):
    """Example strategy with EMA crossover and RSI filter."""

    timeframe = '5m'
    minimal_roi = {"0": 0.03}
    stoploss = -0.1

    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.015

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: Dict) -> pd.DataFrame:
        if ta is None:
            raise ImportError("TA-Lib not available. Install freqtrade with TA-Lib support.")

        dataframe['ema_fast'] = ta.EMA(dataframe['close'], timeperiod=12)
        dataframe['ema_slow'] = ta.EMA(dataframe['close'], timeperiod=26)
        dataframe['rsi'] = ta.RSI(dataframe['close'], timeperiod=14)
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
