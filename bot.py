import ccxt
import ta
import pandas as pd
import numpy as np
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler
import time
import feedparser

# === CONFIGURATION ===
TELEGRAM_BOT_TOKEN = "7600715915:AAFepyDYc0j062lK_ilcPATiSPkPzmQJSXs"
TELEGRAM_GROUP_ID = None  # Replace with your group ID after getting it from /id
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'
RISK = 50
REWARD = 100

bot = Bot(token=TELEGRAM_BOT_TOKEN)
exchange = ccxt.binance()

# === FETCH MARKET DATA ===
def fetch_data(symbol, timeframe='1h'):
    bars = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# === CALCULATE INDICATORS ===
def calculate_indicators(df):
    rsi = ta.momentum.RSIIndicator(close=data['close']).rsi()
    df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)

    high = df['high'].max()
    low = df['low'].min()
    fib_levels = {
        '0.0': low,
        '0.236': low + 0.236 * (high - low),
        '0.382': low + 0.382 * (high - low),
        '0.5': low + 0.5 * (high - low),
        '0.618': low + 0.618 * (high - low),
        '1.0': high
    }
    return df, fib_levels

# === GENERATE SIGNAL ===
def generate_signal():
    try:
        df = fetch_data(SYMBOL, TIMEFRAME)
        df, fib = calculate_indicators(df)

        last = df.iloc[-1]
        rsi = last['RSI']
        macd = last['macd']
        macd_signal = last['macd_signal']
        price = last['close']

        # BUY SIGNAL
        if rsi < 30 and macd > macd_signal and price < fib['0.382']:
            entry = price
            tp = round(entry + REWARD, 2)
            sl = round(entry - RISK, 2)
            rr = round(REWARD / RISK, 2)
            message = f"""🚀 *Buy Signal Detected!*

📈 Pair: {SYMBOL}
💵 Entry: {entry}
🎯 Take Profit: {tp}
🛑 Stop Loss: {sl}
📊 Risk/Reward: {rr}
📍 Confirmed by RSI, MACD, and Fib 0.382
"""
            if TELEGRAM_GROUP_ID:
                bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=message, parse_mode='Markdown')

        # SELL SIGNAL
        elif rsi > 70 and macd < macd_signal and price > fib['0.618']:
            entry = price
            tp = round(entry - REWARD, 2)
            sl = round(entry + RISK, 2)
            rr = round(REWARD / RISK, 2)
            message = f"""🔻 *Sell Signal Detected!*

📉 Pair: {SYMBOL}
💵 Entry: {entry}
🎯 Take Profit: {tp}
🛑 Stop Loss: {sl}
📊 Risk/Reward: {rr}
📍 Confirmed by RSI, MACD, and Fib 0.618
"""
            if TELEGRAM_GROUP_ID:
                bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=message, parse_mode='Markdown')

    except Exception as e:
        print("Error generating signal:", e)

# === GET CHAT ID ===
def get_chat_id(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    update.message.reply_text(f"Chat ID: {chat_id}")

# === FETCH NEWS ===
def fetch_news():
    try:
        sources = [
            "https://www.coindesk.com/arc/outboundfeeds/rss/",
            "https://cointelegraph.com/rss"
        ]

        headlines = []

        for source in sources:
            feed = feedparser.parse(source)
            for entry in feed.entries[:2]:
                headlines.append(f"🗞 {entry.title}\n🔗 {entry.link}")

        news_message = "📰 *Top Crypto Headlines:*\n\n" + "\n\n".join(headlines[:4])
        
        if TELEGRAM_GROUP_ID:
            bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=news_message, parse_mode='Markdown')
    
    except Exception as e:
        print("Error fetching news:", e)

# === START TELEGRAM HANDLER ===
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
dp.add_handler(CommandHandler("id", get_chat_id))
updater.start_polling()

# === SCHEDULE THE SIGNAL & NEWS GENERATOR ===
scheduler = BackgroundScheduler()
scheduler.add_job(generate_signal, 'interval', hours=1)
scheduler.add_job(fetch_news, 'interval', hours=1)
scheduler.start()

# === KEEP RUNNING ===
print("Bot is running... (type /id in your group to get group ID)")
try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()
