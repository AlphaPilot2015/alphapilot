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
# --- Añadir en app/strategy.py ---

from typing import List, Dict, Tuple
import pandas as pd
from .broker import bars_multi

def signals_sma_multi(symbols: List[str], fast=5, slow=20) -> Dict[str, Tuple[str, dict]]:
    """
    Calcula señales SMA para una lista de símbolos con una sola llamada de datos.
    Devuelve: {symbol: (signal, info_dict)}
    """
    out: Dict[str, Tuple[str, dict]] = {}
    data = bars_multi(symbols, limit=max(fast, slow) + 2, tf=TimeFrame.Minute)
    for sym in symbols:
        df = data.get(sym)
        if df is None or df.empty or "close" not in df.columns:
            out[sym] = ("hold", {"reason": "no-data"})
            continue
        c = df["close"].astype(float)
        sma_fast = float(c.rolling(fast).mean().iloc[-1])
        sma_slow = float(c.rolling(slow).mean().iloc[-1])
        last = float(c.iloc[-1])
        if sma_fast > sma_slow:
            sig = "buy"
        elif sma_fast < sma_slow:
            sig = "sell"
        else:
            sig = "hold"
        out[sym] = (sig, {"last": last, "sma_fast": sma_fast, "sma_slow": sma_slow})
    return out

def rebalance_multi(symbols: List[str]) -> Dict[str, dict]:
    """
    Ejecuta buy/sell/hold por símbolo, repartiendo el efectivo entre todos.
    Usa RISK_CASH_PCT como % total, dividido por nº de símbolos.
    """
    sigs = signals_sma_multi(symbols)
    # efectivo total y reparto simple
    cash = get_cash()
    n = max(len(symbols), 1)
    per_symbol_cash = cash * RISK_CASH_PCT / n

    results: Dict[str, dict] = {}
    current = {p["symbol"]: int(float(p["qty"])) for p in positions()}

    for sym in symbols:
        sig, info = sigs.get(sym, ("hold", {}))
        price = float(info.get("last", 0.0) or 0.0)
        held = int(current.get(sym, 0))
        if sig == "buy" and price > 0:
            qty = max(int(per_symbol_cash // price), 0)
            if qty > 0:
                order = submit_market_order(sym, qty, "buy")
                results[sym] = {"action": "buy", "qty": qty, "price": price, "info": info, "order": order}
            else:
                results[sym] = {"action": "hold", "reason": "low-cash", "info": info}
        elif sig == "sell" and held > 0:
            order = submit_market_order(sym, held, "sell")
            results[sym] = {"action": "sell", "qty": held, "price": price, "info": info, "order": order}
        else:
            results[sym] = {"action": "hold", "info": info}
    return results
