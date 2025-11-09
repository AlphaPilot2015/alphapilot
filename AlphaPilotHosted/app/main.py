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
