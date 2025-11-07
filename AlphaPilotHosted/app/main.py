from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import os, datetime

app = FastAPI(title="AlphaPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.datetime.utcnow().isoformat() + "Z"}

@app.get("/api/privacy", response_class=HTMLResponse)
def privacy():
    return """<h1>Privacy Policy</h1><p>AlphaPilot processes data to provide automated investing features. No guarantees of returns. Investing involves risk.</p>"""

@app.get("/api/terms", response_class=HTMLResponse)
def terms():
    return """<h1>Terms of Service</h1><p>Use at your own risk. No guaranteed profits. You are responsible for compliance with local regulations.</p>"""

@app.get("/api/demo")
def demo():
    # Minimal mock response for the landing CTA
    return {"message": "Demo started", "portfolio_id": 1, "equity": 100000.0, "cash": 100000.0, "fees_rate": 0.10}

@app.get("/")
def root():
    return {"app": "AlphaPilot API", "message": "Use /api endpoints or open the web UI on /"}
