# app/broker.py
import os
from typing import Dict, List, Optional
import pandas as pd

# Librería oficial (modo "legacy" estable y sencilla)
from alpaca_trade_api.rest import REST, TimeFrame

# Lee credenciales del entorno (Render → Environment)
APCA_API_KEY_ID = os.getenv("APCA_API_KEY_ID", "")
APCA_API_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY", "")
APCA_API_BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets")

# Instancia única del cliente
_api: Optional[REST] = None


def api() -> REST:
    """Devuelve un cliente REST autenticado (Paper o Live según APCA_API_BASE_URL)."""
    global _api
    if _api is None:
        if not APCA_API_KEY_ID or not APCA_API_SECRET_KEY:
            raise RuntimeError("Faltan credenciales Alpaca (APCA_API_KEY_ID/SECRET_KEY).")
        _api = REST(
            key_id=APCA_API_KEY_ID,
            secret_key=APCA_API_SECRET_KEY,
            base_url=APCA_API_BASE_URL,
            api_version="v2",
        )
    return _api


# ------------------- Datos de mercado -------------------

def bars(symbol: str, limit: int = 200, tf: TimeFrame = TimeFrame.Minute) -> Optional[pd.DataFrame]:
    """
    Devuelve OHLCV en DataFrame con columnas: open, high, low, close, volume (indexado por tiempo).
    """
    try:
        a = api()
        resp = a.get_bars(symbol, tf, limit=limit, adjustment='raw')
        # .df (DataFrame) está disponible en alpaca-trade-api
        df = resp.df.copy()
        if df.empty:
            return None
        # Si pedimos un solo símbolo, el DF puede venir multiindexado por symbol/time
        if isinstance(df.index, pd.MultiIndex):
            # filtra el símbolo y quita el nivel del símbolo
            df = df.xs(symbol, level=0)
        # Unifica nombres a minúsculas
        df = df.rename(
            columns={
                "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"
            }
        )
        return df
    except Exception as e:
        print(f"[broker.bars] error fetching bars for {symbol}: {e}")
        return None


def bars_multi(symbols: List[str], limit: int = 200, tf: TimeFrame = TimeFrame.Minute) -> Dict[str, pd.DataFrame]:
    """
    Descarga barras por símbolo (simple y robusto: 1 request por símbolo).
    Devuelve dict {symbol: DataFrame|None}
    """
    out: Dict[str, pd.DataFrame] = {}
    for sym in symbols:
        out[sym] = bars(sym, limit=limit, tf=tf) or pd.DataFrame()
    return out


# ------------------- Cuenta / posiciones -------------------

def get_cash() -> float:
    """Efectivo disponible en la cuenta (float)."""
    try:
        a = api()
        acc = a.get_account()
        return float(acc.cash or 0.0)
    except Exception as e:
        print(f"[broker.get_cash] error: {e}")
        return 0.0


def positions() -> List[Dict]:
    """Lista de posiciones: [{'symbol': 'AAPL', 'qty': '10', 'avg_entry_price': '...'}, ...]."""
    try:
        a = api()
        poss = a.list_positions()
        out = []
        for p in poss:
            out.append(
                {
                    "symbol": p.symbol,
                    "qty": p.qty,  # string en API; conviértelo a int/float cuando lo uses
                    "avg_entry_price": p.avg_entry_price,
                    "market_value": p.market_value,
                    "unrealized_pl": p.unrealized_pl,
                }
            )
        return out
    except Exception as e:
        print(f"[broker.positions] error: {e}")
        return []


# ------------------- Órdenes -------------------

def submit_market_order(symbol: str, qty: int, side: str, tif: str = "day") -> Dict:
    """
    Envía una orden de mercado. side ∈ {'buy','sell'} ; tif ∈ {'day','gtc'}
    Retorna un dict con los campos principales de la orden.
    """
    side = side.lower().strip()
    if side not in ("buy", "sell"):
        raise ValueError("side debe ser 'buy' o 'sell'")
    if qty <= 0:
        return {"status": "skipped", "reason": "qty<=0"}

    try:
        a = api()
        order = a.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type="market",
            time_in_force=tif,
        )
        return {
            "id": order.id,
            "symbol": order.symbol,
            "qty": order.qty,
            "side": order.side,
            "type": order.type,
            "time_in_force": order.time_in_force,
            "status": order.status,
            "created_at": str(order.created_at),
        }
    except Exception as e:
        print(f"[broker.submit_market_order] error: {e}")
        return {"status": "error", "error": str(e)}
