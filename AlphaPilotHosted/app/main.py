# app/main.py
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import datetime, os

# Carga perezosa de la estrategia para evitar caer en import si falta algo
try:
    from .strategy import signal_sma, rebalance_symbol
except Exception as e:
    signal_sma = None
    rebalance_symbol = None
    _import_error = e
else:
    _import_error = None

app = FastAPI(
    title="AlphaPilot API",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

API_TOKEN = os.getenv("API_TOKEN", "")

def require_token(x_api_key: str | None):
    if not API_TOKEN:
        return  # sin token configurado, no exigimos cabecera
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")

@app.get("/api/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/api/privacy", response_class=HTMLResponse)
def privacy():
    return """<h1>Privacy Policy</h1><p>AlphaPilot processes data to provide automated investing features. No guarantees. Investing involves risk.</p>"""

@app.get("/api/terms", response_class=HTMLResponse)
def terms():
    return """<h1>Terms of Service</h1><p>Use at your own risk. No guaranteed profits. You are responsible for compliance with local regulations.</p>"""

@app.get("/api/demo")
def demo():
    return {"message": "Demo started", "portfolio_id": 1, "equity": 100000.0, "cash": 100000.0, "fees_rate": 0.10}

@app.get("/api/signal")
def api_signal(symbol: str = "AAPL", x_api_key: str | None = Header(None, alias="X-API-KEY")):
    require_token(x_api_key)
    if _import_error:
        raise HTTPException(status_code=500, detail=f"strategy import error: {type(_import_error).__name__}: {str(_import_error)}")
    sig, info = signal_sma(symbol)
    return {"symbol": symbol, "signal": sig, **info}

@app.post("/api/rebalance")
def api_rebalance(symbol: str = "AAPL", x_api_key: str | None = Header(None, alias="X-API-KEY")):
    require_token(x_api_key)
    if _import_error:
        raise HTTPException(status_code=500, detail=f"strategy import error: {type(_import_error).__name__}: {str(_import_error)}")
    return rebalance_symbol(symbol)

@app.get("/")
def root():
    # Página mínima para comprobar que el backend vive
    return JSONResponse({"app": "AlphaPilot API", "message": "Open /api/docs for Swagger; web UI at /"})
