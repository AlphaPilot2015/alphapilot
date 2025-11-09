# app/broker.py
import os
from alpaca_trade_api.rest import REST, TimeFrame, APIError

# 🧩 Cargamos las claves de entorno desde Render
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# 🔌 Conexión al broker Alpaca
api = REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, base_url=ALPACA_BASE_URL)

# ✅ Funciones principales
def account():
    """Devuelve información de la cuenta"""
    return api.get_account()._raw

def positions():
    """Devuelve las posiciones abiertas"""
    return [p._raw for p in api.list_positions()]

def get_cash():
    """Devuelve el efectivo disponible"""
    return float(api.get_account().cash)

def bars(symbol, limit=100, tf=TimeFrame.Minute):
    """Devuelve las últimas velas del símbolo"""
    return api.get_bars(symbol, tf, limit=limit).df

def market_is_open():
    """Comprueba si el mercado está abierto"""
    clock = api.get_clock()
    return bool(clock.is_open)

def submit_market_order(symbol: str, qty: int, side: str):
    """Ejecuta una orden de mercado (compra o venta)"""
    try:
        o = api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type='market',
            time_in_force='day'
        )
        return o._raw
    except APIError as e:
        return {"error": str(e)}
