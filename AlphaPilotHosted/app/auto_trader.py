# app/auto_trader.py
import time
from datetime import datetime
from .strategy import signal_sma, rebalance_symbol, market_is_open

SYMBOL = "AAPL"  # Puedes cambiarlo a otro (TSLA, NVDA, BTC/USD, etc.)
INTERVAL_SECONDS = 1  # Ejecuta cada segundo

def run_bot():
    print("🚀 AlphaPilot AutoTrader iniciado.")
    while True:
        try:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            if market_is_open():
                sig, info = signal_sma(SYMBOL)
                print(f"[{now}] Señal {SYMBOL}: {sig.upper()} | Precio: {info.get('last')}")
                result = rebalance_symbol(SYMBOL)
                print(result)
            else:
                print(f"[{now}] Mercado cerrado.")
            time.sleep(INTERVAL_SECONDS)
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)
