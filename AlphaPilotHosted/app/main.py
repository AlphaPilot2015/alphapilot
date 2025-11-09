import os
import asyncio
import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, status, Header, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.brokers.alpaca import AlpacaClient

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()

async def require_admin_api_key(x_api_key: str = Header(default="")):
    if not ADMIN_API_KEY or x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

app = FastAPI(
    title="AlphaPilot Private API",
    version="0.2.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

alpaca = AlpacaClient(
    key=os.getenv("ALPACA_KEY_ID", ""),
    secret=os.getenv("ALPACA_SECRET_KEY", ""),
    base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets").rstrip("/")
)

STRATEGY_ENABLED = os.getenv("STRATEGY_ENABLED_DEFAULT", "true").lower() == "true"
STRATEGY_SYMBOL = os.getenv("STRATEGY_SYMBOL", "SPY")

_strategy_task: Optional[asyncio.Task] = None
_strategy_stop = asyncio.Event()

async def strategy_loop():
    global STRATEGY_ENABLED
    try:
        while not _strategy_stop.is_set():
            if STRATEGY_ENABLED:
                acct = await alpaca.get_account()
                try:
                    cash = float(acct.get("cash", 0))
                except Exception:
                    cash = 0.0
                if cash >= 100:
                    try:
                        await alpaca.market_order(symbol=STRATEGY_SYMBOL, side="buy", qty=1)
                    except Exception:
                        pass
            try:
                await asyncio.wait_for(_strategy_stop.wait(), timeout=900.0)
            except asyncio.TimeoutError:
                continue
    except Exception:
        pass

@app.on_event("startup")
async def on_startup():
    global _strategy_task, _strategy_stop
    _strategy_stop = asyncio.Event()
    _strategy_task = asyncio.create_task(strategy_loop())

@app.on_event("shutdown")
async def on_shutdown():
    _strategy_stop.set()
    if _strategy_task:
        try:
            await _strategy_task
        except Exception:
            pass

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/api/privacy", response_class=HTMLResponse)
def privacy():
    return "<h1>Privacy Policy</h1><p>Automated investing features. No guarantees of returns. Investing involves risk.</p>"

@app.get("/api/terms", response_class=HTMLResponse)
def terms():
    return "<h1>Terms of Service</h1><p>Use at your own risk. No guaranteed profits. You are responsible for compliance with local regulations.</p>"

@app.get("/api/portfolio", dependencies=[Depends(require_admin_api_key)])
async def portfolio():
    acct = await alpaca.get_account()
    pos = await alpaca.get_positions()
    return {"account": acct, "positions": pos}

@app.post("/api/orders/market", dependencies=[Depends(require_admin_api_key)])
async def orders_market(symbol: str = Query(..., min_length=1), side: str = Query(..., regex="^(buy|sell)$"), qty: float = Query(..., gt=0)):
    resp = await alpaca.market_order(symbol=symbol.upper(), side=side, qty=qty)
    return resp

@app.post("/api/strategy/toggle", dependencies=[Depends(require_admin_api_key)])
async def strategy_toggle(enable: bool):
    global STRATEGY_ENABLED
    STRATEGY_ENABLED = bool(enable)
    return {"enabled": STRATEGY_ENABLED, "symbol": STRATEGY_SYMBOL}

@app.get("/api/fee/preview", dependencies=[Depends(require_admin_api_key)])
async def fee_preview():
    pnl_realizado = 0.0
    fee = round(pnl_realizado * 0.10, 2)
    return {"pnl_realized": pnl_realizado, "fee_10pct": fee}

@app.get("/", response_class=HTMLResponse)
def root():
    return "<h2>AlphaPilot — Private</h2><p>Open <code>/app/dashboard.html</code> and use your X-API-Key.</p>"
