# Simple Telegram Echo Bot

This example shows how to create a basic Telegram bot using the `python-telegram-bot` library.

## Prerequisites
- Python 3.8+
- An API token from [@BotFather](https://core.telegram.org/bots#botfather)

## Setup
```bash
pip install python-telegram-bot --upgrade
export TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
python echo_bot.py
```

The bot responds with the same text you send it.

---

# Crypto Market Bot

A Telegram bot that fetches real-time cryptocurrency prices and predicts short-term trends using Binance data.

## Prerequisites
- Python 3.8+
- `requests` and `python-telegram-bot` libraries
- An API token from [@BotFather](https://core.telegram.org/bots#botfather)

## Setup
```bash
pip install python-telegram-bot requests --upgrade
export TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
python crypto_bot.py
```

Prices are retrieved from the [Binance public API](https://github.com/binance/binance-spot-api-docs). The trend prediction is a simple moving-average comparison and **not** financial advice.

Use `/price BTC` to get the latest Bitcoin price, or `/predict ETH` for a basic trend prediction.
