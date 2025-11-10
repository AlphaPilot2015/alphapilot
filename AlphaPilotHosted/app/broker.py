# app/broker.py
import os, pandas as pd, alpaca_trade_api as tradeapi
from alpaca_trade_api.rest import REST, TimeFrame

APCA_API_KEY_ID     = os.getenv("APCA_API_KEY_ID", "")
APCA_API_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY", "")
APCA_API_BASE_URL   = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

def _rest() -> REST:
    if not (APCA_API_KEY_ID and APCA_API_SECRET_KEY):
        raise RuntimeError("Missing Alpaca API keys")
    return tradeapi.REST(
        key_id=APCA_API_KEY_ID,
        secret_key=APCA_API_SECRET_KEY,
        base_url=APCA_API_BASE_URL
    )

def bars(symbol: str, limit=50, tf: TimeFrame = TimeFrame.Minute) -> pd.DataFrame:
    api = _rest()
    data = api.get_bars(symbol, timeframe=tf, limit=limit).df
    if isinstance(data, pd.DataFrame) and not data.empty:
        if isinstance(data.index, pd.MultiIndex):
            # get_bars con varios símbolos devuelve MultiIndex
            data = data.xs(symbol)
    return data

def positions():
    api = _rest()
    pos = api.list_positions()
    out = []
    for p in pos:
        out.append({"symbol": p.symbol, "qty": p.qty})
    return out

def get_cash() -> float:
    api = _rest()
    acct = api.get_account()
    try:
        return float(acct.cash)
    except Exception:
        return 0.0

def submit_market_order(symbol: str, qty: int, side: str):
    assert side in ("buy", "sell")
    api = _rest()
    o = api.submit_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="market",
        time_in_force="day",
    )
    return {"id": o.id, "status": o.status, "symbol": o.symbol, "qty": o.qty, "side": o.side}
