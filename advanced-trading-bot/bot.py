"""Minimal but extendable crypto trading bot example.

This script illustrates how ccxt can be combined with the freqtrade strategy
interface.  It runs a simple EMA/RSI strategy and includes basic risk
management.  Command line arguments allow you to tweak the trading symbol,
timeframe and other settings without touching the code.

Running it without API keys will operate in dry‑run mode and simply print the
orders it would place.
"""

import argparse
import os
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


def parse_args() -> argparse.Namespace:
    """Return command line arguments."""
    parser = argparse.ArgumentParser(description="Run the example trading bot")
    parser.add_argument("--symbol", default="BTC/USDT",
                        help="Trading pair to operate on")
    parser.add_argument("--timeframe", default="5m",
                        help="Candlestick timeframe")
    parser.add_argument("--risk", type=float, default=0.01,
                        help="Risk percentage per trade (0-1)")
    parser.add_argument("--limit", type=int, default=100,
                        help="Number of candles to fetch")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print orders instead of executing")
    parser.add_argument("--cycles", type=int, default=1,
                        help="Number of iterations to run")
    return parser.parse_args()


def get_exchange() -> ccxt.Exchange:
    """Create a ccxt exchange instance using env vars if available."""
    key = os.getenv("API_KEY")
    secret = os.getenv("API_SECRET")
    params = {"enableRateLimit": True}
    if key and secret:
        params.update({"apiKey": key, "secret": secret})
    return ccxt.binance(params)


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


def run_cycle(exchange: ccxt.Exchange, strategy: AdvancedStrategy, args: argparse.Namespace) -> None:
    """Fetch data, evaluate the strategy and optionally place orders."""
    df = fetch_candles(exchange, args.symbol, args.timeframe, args.limit)
    df = strategy.populate_indicators(df, metadata={})
    df = strategy.populate_entry_trend(df, metadata={})
    df = strategy.populate_exit_trend(df, metadata={})

    last = df.iloc[-1]
    price = last['close']
    balance = exchange.fetch_balance().get('free', {}).get('USDT', 0)

    if last.get('enter_long'):
        stop_distance = price * abs(strategy.stoploss)
        amount = calculate_position_size(balance, args.risk, price, stop_distance)
        if args.dry_run or not exchange.apiKey:
            print(f"Buy signal. Would place order for {amount:.6f} {args.symbol} at {price}")
        else:
            exchange.create_market_buy_order(args.symbol, amount)
            print(f"Placed buy order for {amount:.6f} {args.symbol} at {price}")
    elif last.get('exit_long'):
        if args.dry_run or not exchange.apiKey:
            print("Sell signal. Would exit position.")
        else:
            exchange.create_market_sell_order(args.symbol, balance)
            print("Placed sell order.")
    else:
        print("No trade signal.")


def main() -> None:
    """Entry point for running one or more trading cycles."""
    args = parse_args()
    exchange = get_exchange()
    strategy = AdvancedStrategy()

    for _ in range(args.cycles):
        run_cycle(exchange, strategy, args)


if __name__ == '__main__':
    main()
