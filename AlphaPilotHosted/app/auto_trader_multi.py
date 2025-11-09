# app/auto_trader_multi.py
import os, time
from datetime import datetime
from typing import List
from .strategy import rebalance_multi, market_is_open, refresh_news_bias

SYMBOLS: List[str] = [s.strip().upper() for s in os.getenv("SYMBOLS", "AAPL,MSFT,BTCUSD").split(",") if s.strip()]
INTERVAL_SECONDS = int(os.getenv("LOOP_INTERVAL_SECONDS", "1"))
TRADE_STOCKS_WHEN_CLOSED = os.getenv("TRADE_STOCKS_WHEN_CLOSED", "false").lower() == "true"

def run_bot():
    print(f"🚀 AlphaPilot 24/7 iniciado | {SYMBOLS} | {INTERVAL_SECONDS}s")
    while True:
        try:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            # refresca sesgo de noticias con cadencia corta (pero no cada tick)
            refresh_news_bias()

            # cripto 24/7 (BTCUSD via Alpaca Crypto) y acciones cuando haya mercado
            if market_is_open() or TRADE_STOCKS_WHEN_CLOSED:
                results = rebalance_multi(SYMBOLS)
                print(f"[{now}] Tick => {results}")
            else:
                # Filtra solo cripto si no quieres operar acciones fuera de horario
                crypto = [s for s in SYMBOLS if "USD" in s or "BTC" in s or "ETH" in s]
                if crypto:
                    results = rebalance_multi(crypto)
                    print(f"[{now}] Tick (crypto only) => {results}")
                else:
                    print(f"[{now}] Mercado cerrado para acciones. Sin cripto en lista.")
            time.sleep(INTERVAL_SECONDS)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot()
