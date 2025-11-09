# app/main.py
import os
import datetime
from typing import Optional, Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, status, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# ============
# Config
# ============
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets").rstrip("/")
ALPACA_KEY_ID = os.getenv("ALPACA_KEY_ID", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "").strip()

if not ALPACA_KEY_ID or not ALPACA_SECRET_KEY:
    # No detenemos el arranque, pero avisamos en logs
    print("[WARN] Faltan ALPACA_KEY_ID o ALPACA_SECRET_KEY (Paper).")

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_KEY_ID,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
    "Accept": "application/json",
}

# ============
# Seguridad básica (solo tú)
# ============
async def require_admin_api_key(x_api_key: str = Header(default="")):
    if not ADMIN_API_KEY:
        # Si no hay clave definida en entorno, no exigimos header (modo abierto)
        return
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

# ============
# App
# ============
app = FastAPI(
    title="AlphaPilot Private API",
    version="1.0.0",
    docs_url=None,          # puedes poner "/api/docs" si quieres Swagger
    redoc_url=None,
    openapi_url=None
)

# CORS (por si abres dashboard.html desde el mismo host)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # ajusta si quieres restringir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============
# Helpers HTTP
# ============
async def _get(path: str) -> Dict[str, Any]:
    url = f"{ALPACA_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=HEADERS)
        if r.status_code >= 400:
            # Propaga mensaje claro
            try:
                detail = r.json()
            except Exception:
                detail = {"error": r.text}
            raise HTTPException(status_code=r.status_code, detail=detail)
        return r.json()

async def _post(path: str, payload: dict) -> Dict[str, Any]:
    url = f"{ALPACA_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=payload, headers=HEADERS)
        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = {"error": r.text}
            raise HTTPException(status_code=r.status_code, detail=detail)
        return r.json()

async def _delete(path: str) -> Dict[str, Any]:
    url = f"{ALPACA_BASE_URL}{path}"
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.delete(url, headers=HEADERS)
        if r.status_code >= 400:
            try:
                detail = r.json()
            except Exception:
                detail = {"error": r.text}
            raise HTTPException(status_code=r.status_code, detail=detail)
        return r.json() if r.text else {"ok": True}

# ============
# Rutas públicas
# ============
@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <h2>AlphaPilot — Private</h2>
    <p>API lista. Abre <code>/app/dashboard.html</code> para usar el panel (pega tu <b>X-API-Key</b> si configuraste ADMIN_API_KEY).</p>
    <ul>
      <li>GET /api/account</li>
      <li>GET /api/positions</li>
      <li>GET /api/orders?status=open</li>
      <li>POST /api/orders/market?symbol=SPY&side=buy&qty=1</li>
      <li>POST /api/orders/cancel?order_id=...</li>
    </ul>
    """

@app.get("/api/privacy", response_class=HTMLResponse)
def privacy():
    return "<h1>Privacy Policy</h1><p>Automated investing features. No guarantees of returns. Investing involves risk.</p>"

@app.get("/api/terms", response_class=HTMLResponse)
def terms():
    return "<h1>Terms of Service</h1><p>Use at your own risk. No guaranteed profits. You are responsible for compliance with local regulations.</p>"

# ============
# Rutas privadas (requieren X-API-Key si ADMIN_API_KEY está configurada)
# ============
@app.get("/api/account", dependencies=[Depends(require_admin_api_key)])
async def api_account():
    return await _get("/v2/account")

@app.get("/api/clock", dependencies=[Depends(require_admin_api_key)])
async def api_clock():
    return await _get("/v2/clock")

@app.get("/api/positions", dependencies=[Depends(require_admin_api_key)])
async def api_positions():
    # 200 con array o 404 si no hay posiciones (Alpaca puede devolver 404)
    try:
        data = await _get("/v2/positions")
    except HTTPException as e:
        if e.status_code == 404:
            return []
        raise
    return data

@app.get("/api/orders", dependencies=[Depends(require_admin_api_key)])
async def api_orders(status: str = Query("open")):
    # status: open, closed, all
    return await _get(f"/v2/orders?status={status}")

@app.post("/api/orders/market", dependencies=[Depends(require_admin_api_key)])
async def api_market_order(
    symbol: str = Query(..., min_length=1),
    side: str = Query(..., regex="^(buy|sell)$"),
    qty: float = Query(..., gt=0),
    tif: str = Query("day"),  # time_in_force
):
    payload = {
        "symbol": symbol.upper(),
        "qty": qty,
        "side": side,
        "type": "market",
        "time_in_force": tif
    }
    return await _post("/v2/orders", payload)

@app.post("/api/orders/cancel", dependencies=[Depends(require_admin_api_key)])
async def api_cancel_order(order_id: str = Query(..., min_length=5)):
    return await _delete(f"/v2/orders/{order_id}")

# Sencillo ejemplo de “fee” (placeholder, sin DB aún)
@app.get("/api/fee/preview", dependencies=[Depends(require_admin_api_key)])
def api_fee_preview():
    pnl_realizado = 0.0  # aquí sumarías PnL realizado de tu histórico
    fee = round(pnl_realizado * 0.10, 2)
    return {"pnl_realized": pnl_realizado, "fee_10pct": fee}
