# ============================================================
# 🤖 Nikkei H4 Agent + JOURNAL (FINAL)
# ============================================================

import time
import schedule
import requests
import pandas as pd
import yfinance as yf
import csv
from datetime import datetime
from ta.trend import EMAIndicator, MACD

TELEGRAM_TOKEN = "8791690243:AAEz4AvTx-ZhSpsjgckR1RZ9hudymjWGxeA"
TELEGRAM_CHAT_ID = "7212942537"

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


SYMBOL = "^N225"
INTERVAL = "4h"
LOOKBACK = "400d"

EMA20, EMA50, EMA200 = 20, 50, 200

ZONE_BUFFER = 0.001
OVEREXTENDED_LIMIT = 0.015
FLAG_ATR_RATIO = 0.8
MIN_SCORE = 2


# ================= DATA =================

def get_data():
    df = yf.download(SYMBOL, period=LOOKBACK, interval=INTERVAL)

    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    df = df.astype(float)
    df.dropna(inplace=True)

    return df


# ================= INDICATORS =================

def indicators(df):

    close = df["Close"]

    df["EMA20"] = EMAIndicator(close, EMA20).ema_indicator()
    df["EMA50"] = EMAIndicator(close, EMA50).ema_indicator()
    df["EMA200"] = EMAIndicator(close, EMA200).ema_indicator()

    macd = MACD(close)
    df["MACD"] = macd.macd_diff()

    df["ATR"] = (df["High"] - df["Low"]).rolling(20).mean()

    df["HA_close"] = (df["Open"]+df["High"]+df["Low"]+df["Close"])/4
    df["HA_open"] = df["HA_close"].shift(1)
    df["HA"] = df["HA_close"] > df["HA_open"]

    return df.dropna()


# ================= LOGGER =================

def log_trade(symbol, direction, entry, sl, tp1, tp2, score):

    file = "trades.csv"
    file_exists = False

    try:
        with open(file, "r"):
            file_exists = True
    except:
        file_exists = False

    with open(file, mode="a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "date", "symbol", "direction",
                "entry", "sl", "tp1", "tp2", "score"
            ])

        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            symbol,
            direction,
            round(entry, 2),
            round(sl, 2),
            round(tp1, 2),
            round(tp2, 2),
            score
        ])


# ================= FILTER =================

def market_filter(df):

    ema_now = df["EMA200"].iloc[-1]
    ema_prev = df["EMA200"].iloc[-6]

    slope = (ema_now - ema_prev) / ema_prev

    if abs(slope) < 0.0002:
        return None

    return "LONG" if slope > 0 else "SHORT"


# ================= SETUP =================

def structure(df, d):
    c = df.iloc[-1]
    if d == "LONG":
        return c["Close"] > c["EMA200"] and c["EMA50"] > c["EMA200"]
    else:
        return c["Close"] < c["EMA200"] and c["EMA50"] < c["EMA200"]


def pullback(df):
    for _, r in df.iloc[-7:-1].iterrows():
        if abs(r["Low"] - r["EMA20"]) < r["EMA20"] * ZONE_BUFFER:
            return True
    return False


def no_extreme(df):
    lows = df["Low"].iloc[-6:-1]
    return all(lows.iloc[i] >= lows.iloc[i-1] for i in range(1, len(lows)))


def not_overextended(df):
    c = df.iloc[-1]
    dist = abs(c["Close"] - c["EMA20"]) / c["EMA20"]
    return dist < OVEREXTENDED_LIMIT


# ================= SCORE =================

def score(df):

    s = 0
    h = df["MACD"]

    if h.iloc[-1] > h.iloc[-2] > h.iloc[-3]:
        s += 1

    if h.iloc[-2] < h.iloc[-1] and h.iloc[-2] < h.iloc[-3]:
        s += 1

    rng = df["High"].iloc[-8:-1].max() - df["Low"].iloc[-8:-1].min()
    atr = df["ATR"].iloc[-1]

    if rng < atr * FLAG_ATR_RATIO:
        s += 1

    if df["HA"].iloc[-1] and df["HA"].iloc[-2]:
        s += 1

    return s


# ================= LEVELS =================

def levels(df, d):

    c = df.iloc[-1]
    price = c["Close"]
    atr = c["ATR"]

    high = df["High"].iloc[-6:-1].max()
    low = df["Low"].iloc[-6:-1].min()

    if d == "LONG":
        return price, low, high, high + atr * 1.2
    else:
        return price, high, low, low - atr * 1.2


# ================= MAIN =================

def run():

    df = get_data()
    df = indicators(df)

    d = market_filter(df)
    if not d:
        return

    if not structure(df, d): return
    if not pullback(df): return
    if not no_extreme(df): return
    if not not_overextended(df): return

    sc = score(df)
    if sc < MIN_SCORE:
        return

    entry, sl, tp1, tp2 = levels(df, d)

    log_trade(SYMBOL, d, entry, sl, tp1, tp2, sc)

    msg = f"""
NIKKEI H4

{d}
Score: {sc}/4

ENTRY: {round(entry,2)}
SL: {round(sl,2)}
TP1: {round(tp1,2)}
TP2: {round(tp2,2)}
"""

    send(msg)


# ================= LOOP =================

if __name__ == "__main__":

    run()

    send("BOT DZIAŁA 🚀")

    schedule.every().day.at("00:05").do(run)
    schedule.every().day.at("04:05").do(run)
    schedule.every().day.at("08:05").do(run)
    schedule.every().day.at("12:05").do(run)
    schedule.every().day.at("16:05").do(run)
    schedule.every().day.at("20:05").do(run)

    while True:
        schedule.run_pending()
        time.sleep(60)
