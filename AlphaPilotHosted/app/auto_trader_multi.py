# app/auto_trader_multi.py
import os, time
from datetime import datetime
from typing import List
from .strategy import market_is_open, rebalance_multi

SYMBOLS: List[str] = [s.strip().upper() for s in os.getenv("SYMBOLS", "AAPL,MSFT").split(",") if s.strip()]
INTERVAL_SECONDS = int(os.getenv("LOOP_INTERVAL_SECONDS", "1"))

def run_bot():
    print(f"🚀 AlphaPilot Multi-Asset AutoTrader iniciado | symbols={SYMBOLS} | interval={INTERVAL_SECONDS}s")
    while True:
        try:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            if market_is_open():
                results = rebalance_multi(SYMBOLS)
                print(f"[{now}] Tick => {results}")
            else:
                print(f"[{now}] Mercado cerrado.")
            time.sleep(INTERVAL_SECONDS)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot()
