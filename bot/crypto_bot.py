"""Telegram bot for basic crypto price lookup and trend hints using Binance."""

import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Official REST docs: https://github.com/binance/binance-spot-api-docs

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE = "https://api.binance.com/api/v3"
TIMEOUT = 10

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send /price <symbol> to get the latest price or /predict <symbol> to get a simple trend prediction."
    )

def get_price(symbol: str) -> float:
    """Return the current price for ``symbol`` quoted in USDT."""
    resp = requests.get(
        f"{API_BASE}/ticker/price",
        params={"symbol": symbol.upper() + "USDT"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return float(data["price"])

def get_prediction(symbol: str) -> str:
    """Return a simple short-term trend based on moving averages."""
    resp = requests.get(
        f"{API_BASE}/klines",
        params={"symbol": symbol.upper() + "USDT", "interval": "1m", "limit": 20},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    candles = resp.json()
    closes = [float(c[4]) for c in candles]
    ma_short = sum(closes[-5:]) / 5
    ma_long = sum(closes[-10:]) / 10
    if ma_short > ma_long:
        return "upward"
    elif ma_short < ma_long:
        return "downward"
    else:
        return "sideways"

async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /price <symbol>")
        return
    symbol = context.args[0]
    try:
        price = get_price(symbol)
        await update.message.reply_text(f"{symbol.upper()} price: ${price:.2f}")
    except requests.HTTPError:
        await update.message.reply_text("Invalid symbol or API error.")
    except Exception as e:
        await update.message.reply_text(f"Error fetching price: {e}")

async def predict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /predict <symbol>")
        return
    symbol = context.args[0]
    try:
        trend = get_prediction(symbol)
        await update.message.reply_text(
            f"Predicted short-term trend for {symbol.upper()}: {trend}"
        )
    except requests.HTTPError:
        await update.message.reply_text("Invalid symbol or API error.")
    except Exception as e:
        await update.message.reply_text(f"Error making prediction: {e}")

def main():
    if not TOKEN:
        raise RuntimeError("Please set the TELEGRAM_BOT_TOKEN environment variable")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("predict", predict_cmd))
    app.run_polling()

if __name__ == "__main__":
    main()
