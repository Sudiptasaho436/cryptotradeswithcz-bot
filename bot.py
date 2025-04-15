import asyncio
import ccxt
import ta
import pandas as pd
import numpy as np
import feedparser
import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import nest_asyncio

# Apply patch to avoid event loop issues
nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)

# Configuration
TELEGRAM_BOT_TOKEN = "7600715915:AAFepyDYc0j062lK_ilcPATiSPkPzmQJSXs"
TELEGRAM_GROUP_ID = 752461685
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'
RISK = 50
REWARD = 100

exchange = ccxt.binance()

# Fetch market data
def fetch_data(symbol, timeframe='1h'):
    bars = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

# Calculate indicators
def calculate_indicators(df):
    df['RSI'] = ta.momentum.RSIIndicator(close=df['close']).rsi()
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_hist'] = macd.macd_diff()

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

# Generate signal
async def generate_signal(bot: Bot):
    try:
        df = fetch_data(SYMBOL, TIMEFRAME)
        df, fib = calculate_indicators(df)

        last = df.iloc[-1]
        rsi = last['RSI']
        macd = last['macd']
        macd_signal = last['macd_signal']
        price = last['close']

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
📍 Confirmed by RSI, MACD, and Fib 0.382"""
            await bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=message, parse_mode='Markdown')

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
📍 Confirmed by RSI, MACD, and Fib 0.618"""
            await bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=message, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Signal error: {e}")

# Fetch news
async def fetch_news(bot: Bot):
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
        await bot.send_message(chat_id=TELEGRAM_GROUP_ID, text=news_message, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"News error: {e}")

# Command Handlers
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Chat ID: {chat_id}")

async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = """
📘 Available Commands:
/id - Get your group ID
/signal - Trigger trade signal
/news - Get latest crypto news
/help - Show this help message
"""
    await update.message.reply_text(help_msg)

async def manual_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Generating signal...")
    await generate_signal(context.bot)

async def manual_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching latest crypto news...")
    await fetch_news(context.bot)

# Main function
async def main():
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("id", get_chat_id))
    application.add_handler(CommandHandler("help", get_help))
    application.add_handler(CommandHandler("signal", manual_signal))
    application.add_handler(CommandHandler("news", manual_news))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(generate_signal(application.bot)), 'interval', hours=1)
    scheduler.add_job(lambda: asyncio.create_task(fetch_news(application.bot)), 'interval', hours=1)
    scheduler.start()

    print("Bot is running... (type /id in your group to get group ID)")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())



 




    
        
    
