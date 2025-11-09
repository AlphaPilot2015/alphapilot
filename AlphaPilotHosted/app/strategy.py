# app/strategy.py
import math, os
from alpaca_trade_api.rest import TimeFrame
from .broker import bars, get_cash, positions, submit_market_order

# % de efectivo a usar por operación (configurable por env)
RISK_CASH_PCT = float(os.getenv("RISK_CASH_PCT", "0.2"))

def _sma(series, n):
    return series.rolling(n).mean()

def signal_sma(symbol: str, fast=5, slow=20):
    """Señal por cruce de medias en velas de 1 minuto."""
    df = bars(symbol, limit=max(fast, slow) + 2, tf=TimeFrame.Minute)
    if df is None or df.empty or "close" not in df.columns:
        return "hold", {"reason": "no-data"}
    c = df["close"].astype(float)
    sma_fast = float(_sma(c, fast).iloc[-1])
    sma_slow = float(_sma(c, slow).iloc[-1])
    last = float(c.iloc[-1])

    if sma_fast > sma_slow:
        sig = "buy"
    elif sma_fast < sma_slow:
        sig = "sell"
    else:
        sig = "hold"

    return sig, {"last": last, "sma_fast": sma_fast, "sma_slow": sma_slow}

def _desired_qty(cash: float, price: float, risk_pct: float = RISK_CASH_PCT):
    if price <= 0: return 0
    alloc = cash * risk_pct
    return max(int(alloc // price), 0)

def rebalance_symbol(symbol: str):
    """Ejecuta acción según señal: buy/sell/hold."""
    sig, info = signal_sma(symbol)
    # posiciones actuales
    held = 0
    for p in positions():
        if p["symbol"] == symbol:
            held = int(float(p["qty"]))
            break

    price = info.get("last", 0.0)
    cash = get_cash()

    if sig == "buy":
        qty = _desired_qty(cash, price)
        if qty > 0:
            order = submit_market_order(symbol, qty, "buy")
            return {"symbol": symbol, "action": "buy", "qty": qty, "price": price, "info": info, "order": order}
        return {"symbol": symbol, "action": "hold", "reason": "no-cash-or-low-price", "info": info}

    if sig == "sell" and held > 0:
        order = submit_market_order(symbol, held, "sell")
        return {"symbol": symbol, "action": "sell", "qty": held, "price": price, "info": info, "order": order}

    return {"symbol": symbol, "action": "hold", "info": info}
