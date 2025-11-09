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

