import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="AlphaPilot API",
    version="0.1.1",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/api/demo")
def demo():
    return {"message": "Demo started", "portfolio_id": 1, "equity": 100000.0, "cash": 100000.0, "fees_rate": 0.10}

@app.get("/api/privacy", response_class=HTMLResponse)
def privacy():
    return "<h1>Privacy Policy</h1><p>AlphaPilot processes data. Investing involves risk.</p>"

@app.get("/api/terms", response_class=HTMLResponse)
def terms():
    return "<h1>Terms</h1><p>Use at your own risk. No guaranteed profits.</p>"

# Página raíz simple (opcional)
@app.get("/")
def root():
    return {"app": "AlphaPilot API", "use": "open /app/dashboard.html for UI"}
