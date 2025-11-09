# app/main.py
import os
import datetime
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

# IMPORTA la estrategia (asegúrate de tener app/strategy.py creado)
from .strategy import signal_sma, rebalance_symbol

app = FastAPI(
    title="AlphaPilot API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

# ========= Protección por token (X-API-KEY) =========
API_TOKEN = os.getenv("API_TOKEN", "")

def require_token(x_api_key: str | None):
    """
    Si has puesto API_TOKEN en Render, exigimos ese valor en el header X-API-KEY.
    Si no hay API_TOKEN definido, no exigimos nada (no recomendado en producción).
    """
    if not API_TOKEN:
        return
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")

# ========= Endpoints que ya tenías =========
@app.get("/api/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/api/privacy", response_class=HTMLResponse)
def privacy():
    return """<h1>Privacy Policy</h1>
<p>AlphaPilot processes data to provide automated investing features. No guarantees of returns. Investing involves risk.</p>"""

@app.get("/api/terms", response_class=HTMLResponse)
def terms():
    return """<h1>Terms of Service</h1>
<p>Use at your own risk. No guaranteed profits. You are responsible for compliance with local regulations.</p>"""

@app.get("/api/demo")
def demo():
    # Respuesta de ejemplo para el CTA del landing
    return {"message": "Demo started", "portfolio_id": 1, "equity": 100000.0, "cash": 100000.0, "fees_rate": 0.10}

@app.get("/")
def root():
    return {"app": "AlphaPilot API", "message": "Use /api endpoints or open the web UI on /"}

# ========= NUEVOS endpoints de trading/estrategia =========
@app.get("/api/signal")
def api_signal(symbol: str = "AAPL", x_api_key: str = Header(None, alias="X-API-KEY")):
    """
    Devuelve la señal de la estrategia (buy/sell/hold) y métricas (SMA).
    """
    require_token(x_api_key)
    sig, info = signal_sma(symbol)
    return {"symbol": symbol, "signal": sig, **info}

@app.post("/api/rebalance")
def api_rebalance(symbol: str = "AAPL", x_api_key: str = Header(None, alias="X-API-KEY")):
    """
    Ejecuta la acción según la señal (buy/sell/hold) para 'symbol'.
    Si compra o vende, envía orden de mercado a Alpaca Paper.
    """
    require_token(x_api_key)
    return rebalance_symbol(symbol)

# --- imports nuevos arriba de todo ---
from fastapi import Header, HTTPException, Body
from typing import List, Dict, Any
import os

from .strategy import (
    signal_sma, signals_sma_multi, blended_signal, news_bias_for, refresh_news_bias,
    rebalance_symbol, rebalance_multi
)
from .broker import positions, get_cash

# --- auth por token simple ---
API_TOKEN = os.getenv("API_TOKEN", "")

def require_token(x_api_key: str | None):
    if not API_TOKEN:
        return
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")

# ------------------- ENDPOINTS NUEVOS -------------------

@app.get("/api/signal_multi")
def api_signal_multi(
    symbols: str = "AAPL,MSFT,BTCUSD",
    x_api_key: str = Header(None, alias="X-API-KEY")
):
    """Señales SMA para varios símbolos de una sola vez."""
    require_token(x_api_key)
    syms = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    data = signals_sma_multi(syms)
    # normaliza respuesta a {symbol:{signal, ...}}
    out: Dict[str, Any] = {}
    for sym, tup in data.items():
        sig, info = tup
        out[sym] = {"signal": sig, **(info or {})}
    return out

@app.get("/api/blended_signal")
def api_blended_signal(
    symbol: str = "AAPL",
    x_api_key: str = Header(None, alias="X-API-KEY")
):
    """Señal combinada (técnico + sesgo noticias)."""
    require_token(x_api_key)
    sig, info = blended_signal(symbol)
    return {"symbol": symbol, "signal": sig, **info}

@app.get("/api/news_bias")
def api_news_bias(
    symbol: str = "AAPL",
    x_api_key: str = Header(None, alias="X-API-KEY")
):
    """Devuelve el sesgo actual por noticias para un símbolo."""
    require_token(x_api_key)
    b = news_bias_for(symbol)
    return {"symbol": symbol, "news_bias": b}

@app.post("/api/rebalance_multi")
def api_rebalance_multi(
    payload: Dict[str, Any] = Body(...),
    x_api_key: str = Header(None, alias="X-API-KEY")
):
    """
    Fuerza un rebalance sobre varios símbolos.
    Body JSON: { "symbols": ["AAPL","MSFT","BTCUSD"] }
    """
    require_token(x_api_key)
    syms = payload.get("symbols") or []
    if not syms:
        raise HTTPException(400, "symbols required")
    syms = [str(s).strip().upper() for s in syms if str(s).strip()]
    return rebalance_multi(syms)

@app.get("/api/portfolio")
def api_portfolio(x_api_key: str = Header(None, alias="X-API-KEY")):
    """Resumen rápido de cash y posiciones."""
    require_token(x_api_key)
    return {"cash": get_cash(), "positions": positions()}

# Influencers configurables vía env; expón lectura/escritura en caliente (memoria)
_INFLUENCERS_MEM: List[str] | None = None

@app.get("/api/influencers")
def api_influencers(x_api_key: str = Header(None, alias="X-API-KEY")):
    require_token(x_api_key)
    global _INFLUENCERS_MEM
    current = _INFLUENCERS_MEM
    if current is None:
        env_val = os.getenv("INFLUENCERS", "trump,powell,elon musk")
        current = [s.strip() for s in env_val.split(",") if s.strip()]
        _INFLUENCERS_MEM = current
    return {"influencers": current}

@app.post("/api/influencers")
def api_set_influencers(
    payload: Dict[str, Any] = Body(...),
    x_api_key: str = Header(None, alias="X-API-KEY")
):
    """
    Body JSON: { "influencers": ["trump", "powell", "elon musk", "yellen"] }
    Esto solo guarda en memoria del proceso (suficiente para Render mientras está vivo).
    """
    require_token(x_api_key)
    global _INFLUENCERS_MEM
    arr = payload.get("influencers") or []
    if not isinstance(arr, list):
        raise HTTPException(400, "influencers must be a list of strings")
    _INFLUENCERS_MEM = [str(s).strip() for s in arr if str(s).strip()]
    # provoca refresco de sesgo en la próxima llamada
    refresh_news_bias()
    return {"ok": True, "influencers": _INFLUENCERS_MEM}
