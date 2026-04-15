import yfinance as yf
import pandas as pd
import ta
import requests
import schedule
import time

# ======================
# TELEGRAM
# ======================
TOKEN = "8791690243:AAEz4AvTx-ZhSpsjgckR1RZ9hudymjWGxeA"
CHAT_ID = "7212942537"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ======================
# GLOBAL
# ======================
signals_today = 0
wins = 0
losses = 0
balance = 1000
last_signal_price = None
last_signal_type = None

# ======================
# DATA (NAPRAWIONE)
# ======================
def get_data():
    df = yf.download("^N225", period="5d", interval="1h")

    # 🔥 FIX NA BŁĄD PANDAS
    df["Close"] = df["Close"].squeeze()
    df["High"] = df["High"].squeeze()
    df["Low"] = df["Low"].squeeze()

    df["EMA50"] = ta.trend.ema_indicator(df["Close"], window=50)
    df["EMA200"] = ta.trend.ema_indicator(df["Close"], window=200)
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
    df["ATR"] = ta.volatility.average_true_range(
        df["High"], df["Low"], df["Close"], window=14
    )

    return df.dropna()

# ======================
# TRADE RESULT
# ======================
def check_trade_result(current_price):
    global wins, losses, balance, last_signal_price, last_signal_type

    if last_signal_price is None:
        return

    diff = current_price - last_signal_price

    if last_signal_type == "BUY":
        if diff > 0:
            wins += 1
            balance += 10
        else:
            losses += 1
            balance -= 10

    elif last_signal_type == "SELL":
        if diff < 0:
            wins += 1
            balance += 10
        else:
            losses += 1
            balance -= 10

    last_signal_price = None
    last_signal_type = None

# ======================
# SIGNAL
# ======================
def check_signal(df):
    global signals_today, last_signal_price, last_signal_type

    last = df.iloc[-1]
    price = round(last["Close"], 2)

    check_trade_result(price)

    if last["EMA50"] > last["EMA200"] and last["RSI"] < 30:
        signals_today += 1
        last_signal_price = price
        last_signal_type = "BUY"

        msg = f"""
🚀 BUY SIGNAL JP225

💰 Cena: {price}
📈 Trend: LONG
📊 RSI: {round(last['RSI'], 2)}
"""
        send_telegram(msg)

    elif last["EMA50"] < last["EMA200"] and last["RSI"] > 70:
        signals_today += 1
        last_signal_price = price
        last_signal_type = "SELL"

        msg = f"""
🔻 SELL SIGNAL JP225

💰 Cena: {price}
📉 Trend: SHORT
📊 RSI: {round(last['RSI'], 2)}
"""
        send_telegram(msg)

# ======================
# MARKET OPEN
# ======================
def send_market_open(df):
    last = df.iloc[-1]

    price = round(last["Close"], 2)
    trend = "LONG" if last["EMA50"] > last["EMA200"] else "SHORT"
    atr = round(last["ATR"], 2)

    msg = f"""
📊 START DNIA JP225

💰 Cena: {price}
📈 Trend: {trend}
📊 ATR: {atr}

💼 Kapitał: {balance}
"""
    send_telegram(msg)

# ======================
# MARKET CLOSE
# ======================
def send_market_close(df):
    global signals_today, wins, losses, balance

    last = df.iloc[-1]

    price = round(last["Close"], 2)
    trend = "LONG" if last["EMA50"] > last["EMA200"] else "SHORT"
    atr = round(last["ATR"], 2)

    total = wins + losses
    winrate = round((wins / total) * 100, 2) if total > 0 else 0

    msg = f"""
📊 KONIEC DNIA JP225

💰 Cena: {price}
📈 Trend: {trend}
📊 ATR: {atr}

📊 Sygnały: {signals_today}
✅ Win: {wins}
❌ Loss: {losses}
📈 Winrate: {winrate}%

💼 Kapitał: {balance}
"""
    send_telegram(msg)

# ======================
# RESET
# ======================
def reset_daily_stats():
    global signals_today
    signals_today = 0

# ======================
# MAIN LOOP
# ======================
def run():
    df = get_data()
    check_signal(df)

# ======================
# SCHEDULE (UTC!)
# ======================
schedule.every(1).hours.do(run)

# 🔥 dostosowane do PL czasu
schedule.every().day.at("04:00").do(lambda: send_market_open(get_data()))
schedule.every().day.at("20:00").do(lambda: send_market_close(get_data()))
schedule.every().day.at("20:01").do(reset_daily_stats)

# ======================
# LOOP
# ======================
while True:
    schedule.run_pending()
    time.sleep(60)
