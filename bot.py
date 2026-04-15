import yfinance as yf
import pandas as pd
import ta
import requests
import schedule
import time

# ======================
# TELEGRAM
# ======================
TOKEN = "TU_WKLEJ_TOKEN"
CHAT_ID = "TU_WKLEJ_CHAT_ID"

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

# ======================
# GLOBAL
# ======================
signals_today = 0

# ======================
# DATA
# ======================
def get_data():
    df = yf.download("^N225", period="5d", interval="1h")

    df["EMA50"] = ta.trend.ema_indicator(df["Close"], window=50)
    df["EMA200"] = ta.trend.ema_indicator(df["Close"], window=200)
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
    df["ATR"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14)

    return df.dropna()

# ======================
# SIGNAL
# ======================
def check_signal(df):
    global signals_today

    last = df.iloc[-1]

    if last["EMA50"] > last["EMA200"] and last["RSI"] < 30:
        signals_today += 1
        msg = f"""
🚀 BUY SIGNAL JP225

💰 Cena: {round(last['Close'], 2)}
📈 Trend: LONG
📊 RSI: {round(last['RSI'], 2)}
"""
        send_telegram(msg)

    elif last["EMA50"] < last["EMA200"] and last["RSI"] > 70:
        signals_today += 1
        msg = f"""
🔻 SELL SIGNAL JP225

💰 Cena: {round(last['Close'], 2)}
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
📊 Dzień dobry — start dnia JP225

💰 Cena: {price}
📈 Trend: {trend}
📊 ATR: {atr}

🧠 Status: oczekiwanie na setup
"""
    send_telegram(msg)

# ======================
# MARKET CLOSE
# ======================
def send_market_close(df):
    global signals_today

    last = df.iloc[-1]

    price = round(last["Close"], 2)
    trend = "LONG" if last["EMA50"] > last["EMA200"] else "SHORT"
    atr = round(last["ATR"], 2)

    msg = f"""
📊 Koniec dnia JP225

💰 Cena końcowa: {price}
📈 Trend: {trend}
📊 ATR: {atr}

📊 Sygnały dziś: {signals_today}

🧠 Status: dzień zakończony
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
# SCHEDULE
# ======================
schedule.every(1).hours.do(run)

schedule.every().day.at("06:00").do(lambda: send_market_open(get_data()))
schedule.every().day.at("22:00").do(lambda: send_market_close(get_data()))
schedule.every().day.at("22:01").do(reset_daily_stats)

# ======================
# LOOP
# ======================
while True:
    schedule.run_pending()
    time.sleep(60)
