import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7600715915:AAFepyDYc0j062lK_ilcPATiSPkPzmQJSXs"

logging.basicConfig(level=logging.INFO)

# --- Helper Functions ---

def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return f"Current price of {symbol.upper()} is ${data['price']}"
    else:
        return "Coin not found or error fetching price."

def get_news():
    # Example from CryptoPanic API (Replace with your token if needed)
    url = "https://cryptopanic.com/api/v1/posts/?auth_token=demo&public=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        news_items = data.get("results", [])[:5]
        return "\n\n".join([f"{item['title']}\n{item['url']}" for item in news_items])
    return "Error fetching news."

def generate_signal(symbol):
    # Placeholder auto signal (basic logic)
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}USDT&interval=1h&limit=14"
    response = requests.get(url)
    if response.status_code == 200:
        data = [float(candle[4]) for candle in response.json()]
        avg_price = sum(data) / len(data)
        last_price = data[-1]
        trend = "LONG" if last_price > avg_price else "SHORT"
        return f"Signal for {symbol.upper()}: {trend} \nEntry: {last_price}"
    return "Signal error: Invalid symbol or data."

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to SmartTrade AI Bot! Use /price BTC, /signal ETH, /news")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        coin = context.args[0]
        msg = get_price(coin)
    else:
        msg = "Please provide a coin symbol. Example: /price BTC"
    await update.message.reply_text(msg)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_news())

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        coin = context.args[0]
        msg = generate_signal(coin)
    else:
        msg = "Please provide a coin symbol. Example: /signal BTC"
    await update.message.reply_text(msg)

# --- Main Bot ---

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("price", price))
app.add_handler(CommandHandler("news", news))
app.add_handler(CommandHandler("signal", signal))

app.run_polling()
