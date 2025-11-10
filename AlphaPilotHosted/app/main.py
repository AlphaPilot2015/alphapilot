from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import datetime, os

from .strategy import signal_sma
from .broker import get_cash, positions

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
        return
    if x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API token")

@app.get("/")
def root():
    return {"app": "AlphaPilot API", "message": "Use /api endpoints or open the web UI on /"}

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/api/demo")
def demo():
    return {"message": "Demo started", "portfolio_id": 1, "equity": 100000.0, "cash": 100000.0, "fees_rate": 0.10}

@app.get("/api/portfolio")
def api_portfolio(x_api_key: str | None = Header(None, alias="X-API-KEY")):
    require_token(x_api_key)
    return {
        "cash": get_cash(),
        "positions": positions(),
    }

@app.get("/api/signal")
def api_signal(symbol: str = "AAPL", x_api_key: str | None = Header(None, alias="X-API-KEY")):
    require_token(x_api_key)
    sig, info = signal_sma(symbol)
    return {"symbol": symbol, "signal": sig, **info}
