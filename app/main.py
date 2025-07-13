from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import httpx

from app.routes.transaction_route import router as transaction_router
from app.routes.merchant_route import router as merchant_router
from app.routes.terminal_route import router as terminal_router
from app.routes.cards_route import router as cards_router
from app.routes.home_route import router as home_router  # New import
from app.routes.schemerouting_route import router as schemerouting_router  # New import for scheme routing
from app.routes.auth_route import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()

app = FastAPI(title="Transaction Acquirer System", lifespan=lifespan)

# Enable CORS for frontend development (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to specific origins (e.g., ["http://localhost:3000"]) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/view_templates")
app.templates = templates

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(home_router)  # Add home router
app.include_router(transaction_router, prefix="/transaction")
app.include_router(merchant_router, prefix="/merchant")
app.include_router(terminal_router, prefix="/terminal")
app.include_router(cards_router, prefix="/card")
app.include_router(schemerouting_router, prefix="/schemerouting")  # Add scheme routing router
app.include_router(auth_router, prefix="/auth")

# Catch-all for Chrome devTools /.well-known/ requests
@app.get("/.well-known/{path:path}")
async def well_known():
    return {"detail": "Not Found"}