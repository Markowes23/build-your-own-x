import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE = "https://api.binance.com/api/v3"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send /price <symbol> to get the latest price or /predict <symbol> to get a simple trend prediction."
    )

def get_price(symbol: str) -> float:
    resp = requests.get(f"{API_BASE}/ticker/price", params={"symbol": symbol.upper() + "USDT"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return float(data["price"])

def get_prediction(symbol: str) -> str:
    resp = requests.get(
        f"{API_BASE}/klines",
        params={"symbol": symbol.upper() + "USDT", "interval": "1m", "limit": 10},
        timeout=10,
    )
    resp.raise_for_status()
    candles = resp.json()
    closes = [float(c[4]) for c in candles]
    sma = sum(closes[:-1]) / (len(closes) - 1)
    last_price = closes[-1]
    if last_price > sma:
        return "upward"
    elif last_price < sma:
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
    except Exception as e:
        await update.message.reply_text(f"Error fetching price: {e}")

async def predict_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /predict <symbol>")
        return
    symbol = context.args[0]
    try:
        trend = get_prediction(symbol)
        await update.message.reply_text(f"Predicted short-term trend for {symbol.upper()}: {trend}")
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
