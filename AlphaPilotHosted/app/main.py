# app/main.py
import datetime
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(
    title="AlphaPilot API",
    version="0.1.1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)
import os
from fastapi import Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

# CORS para que el frontend pueda llamar a la API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # si quieres, cámbialo a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Seguridad muy simple para uso personal ---
API_TOKEN = os.getenv("API_TOKEN", "")

def require_token(x_api_key: str = Header(default="")):
    if API_TOKEN and x_api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

# --- Cliente Alpaca ---
ALPACA_KEY_ID = os.getenv("ALPACA_KEY_ID")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

if not (ALPACA_KEY_ID and ALPACA_SECRET_KEY):
    print("[WARN] Falta configurar ALPACA_KEY_ID/ALPACA_SECRET_KEY en Render")

trading = TradingClient(
    api_key=ALPACA_KEY_ID,
    secret_key=ALPACA_SECRET_KEY,
    paper=True,  # asegura paper
    base_url=ALPACA_BASE_URL,
)

# --- Modelos ---
class PlaceOrderBody(BaseModel):
    symbol: str
    qty: int
    side: str  # "buy" | "sell"
    tif: str = "day"  # time in force: day, gtc, etc.

# --- Rutas privadas (requieren X-API-KEY) ---
@app.get("/api/account")
def get_account(_: bool = Depends(require_token)):
    acc = trading.get_account()
    return {
        "id": acc.id,
        "cash": acc.cash,
        "portfolio_value": acc.portfolio_value,
        "buying_power": acc.buying_power,
        "status": acc.status,
    }

@app.get("/api/positions")
def get_positions(_: bool = Depends(require_token)):
    pos = trading.get_all_positions()
    return [p.__dict__ for p in pos]

@app.get("/api/orders")
def get_orders(_: bool = Depends(require_token)):
    orders = trading.get_orders()
    return [o.__dict__ for o in orders]

@app.post("/api/order")
def place_order(body: PlaceOrderBody, _: bool = Depends(require_token)):
    side = OrderSide.BUY if body.side.lower() == "buy" else OrderSide.SELL
    req = MarketOrderRequest(
        symbol=body.symbol.upper(),
        qty=body.qty,
        side=side,
        time_in_force=TimeInForce(body.tif.upper()),
    )
    order = trading.submit_order(req)
    return {"id": order.id, "status": order.status, "symbol": order.symbol, "qty": order.qty}
# Router con prefijo /api
api = APIRouter(prefix="/api")

@api.get("/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@api.get("/privacy", response_class=HTMLResponse)
def privacy():
    return """<h1>Privacy Policy</h1>
<p>AlphaPilot processes data to provide automated investing features.
No guarantees of returns. Investing involves risk.</p>"""

@api.get("/terms", response_class=HTMLResponse)
def terms():
    return """<h1>Terms of Service</h1>
<p>Use at your own risk. No guaranteed profits.
You are responsible for compliance with local regulations.</p>"""

@api.get("/demo")
def demo():
    return {
        "message": "Demo started",
        "portfolio_id": 1,
        "equity": 100000.0,
        "cash": 100000.0,
        "fees_rate": 0.10,
    }

# montar el router /api
app.include_router(api)

# ping básico para la raíz (opcional)
@app.get("/")
def root():
    return {"app": "AlphaPilot", "status": "ok"}

