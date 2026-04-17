import yfinance as yf
import pandas as pd
import ta
import requests
import schedule
import time
from datetime import datetime

# ====================
# TELEGRAM
# ====================
TOKEN = "8791690243:AAEz4AvTx-ZhSpsjgckR1RZ9hudymjWGxeA"
CHAT_ID = "7212942537"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print("Telegram error:", e)

# ====================
# GLOBAL
# ====================
signals_today = 0
wins = 0
losses = 0

# ====================
# DATA
# ====================
def get_data():
    try:
        df = yf.download("^N225", period="5d", interval="1h")

        if df is None or df.empty:
            return None

        close = df["Close"]

        # 🔥 FIX NA TWÓJ BŁĄD
        if hasattr(close, "shape") and len(close.shape) > 1:
            close = close.squeeze()

        df["EMA50"] = ta.trend.ema_indicator(close, window=50)

        return df

    except Exception as e:
        print("DATA ERROR:", e)
        return None

# ====================
# MARKET START
# ====================
def market_open():
    df = get_data()

    if df is None:
        send_telegram("❌ Błąd danych - brak startu")
        return

    price = df["Close"].iloc[-1]

    send_telegram(f"""📈 Dzień dobry!
Start rynku JP225

Cena: {price}
Sygnały: {signals_today}
Balans: demo

🚀 Bot działa""")

# ====================
# MARKET CLOSE
# ====================
def market_close():
    send_telegram(f"""📉 Koniec dnia

Sygnały: {signals_today}
Wins: {wins}
Losses: {losses}

Bot kończy pracę""")

# ====================
# SCHEDULE
# ====================
schedule.every().day.at("06:00").do(market_open)
schedule.every().day.at("22:00").do(market_close)

# TEST START
send_telegram("✅ BOT URUCHOMIONY")

# ====================
# LOOP
# ====================
while True:
    schedule.run_pending()
    time.sleep(1)
