from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import httpx
import time
import logging  # Import logging module
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import session_store, SESSION_COOKIE_NAME, SESSION_EXPIRATION_SECONDS
from app.routes.auth_route import router as auth_router
from app.routes.users_route import router as users_router
from app.routes.transaction_route import router as transaction_router
from app.routes.merchant_route import router as merchant_router
from app.routes.terminal_route import router as terminal_router
from app.routes.cards_route import router as cards_router
from app.routes.schemerouting_route import router as schemerouting_router
from app.utils import get_current_user
from app.routes.home_route import router as home_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Initialize logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = httpx.AsyncClient()
    yield
    await app.requests_client.aclose()

app = FastAPI(title="Transaction Acquirer System", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="app/view_templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Custom authentication middleware
@app.middleware("http")
async def require_authentication(request: Request, call_next):
    public_paths = ["/login", "/auth/login", "/auth/logout", "/"]
    if request.url.path in public_paths or request.url.path.startswith("/static"):
        logger.info(f"Allowing public path: {request.url.path}")
        return await call_next(request)
    
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id or session_id not in session_store:
        logger.info("Unauthorized: No valid session, redirecting to /")
        return RedirectResponse(url="/")
    
    session_data = session_store[session_id]
    if time.time() > session_data.get("expires_at", 0):
        logger.info("Session expired, redirecting to /")
        del session_store[session_id]
        return RedirectResponse(url="/")
    
    logger.info(f"Authenticated request for path: {request.url.path}")
    return await call_next(request)

# Routes
app.include_router(home_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/users")
app.include_router(transaction_router, prefix="/transaction")
app.include_router(merchant_router, prefix="/merchant")
app.include_router(terminal_router, prefix="/terminal")
app.include_router(cards_router, prefix="/card")
app.include_router(schemerouting_router, prefix="/schemerouting")

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    logger.info("Rendering login page")
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.get("/dashboard")
async def dashboard_page(request: Request, user=Depends(get_current_user)):
    if not user:
        logger.info("Unauthorized access to /dashboard, redirecting to /")
        return RedirectResponse("/")
    logger.info(f"Rendering dashboard for user: {user['username']}")
    return HTMLResponse("<h1>Welcome to the Dashboard!</h1><p>You are authenticated.</p><a href='/auth/logout'>Logout</a>")