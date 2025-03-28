from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from .routes import twilio_routes, calendar_routes, auth
from .middleware import auth_middleware
from .lib.firebase import initialize_firebase
import logging
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Initialize Firebase
initialize_firebase()

# Get allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(twilio_routes.router, prefix="/api/twilio", tags=["twilio"])
app.include_router(calendar_routes.router, prefix="/api/calendar", tags=["calendar"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# Debug endpoint to list all routes
@app.get("/debug/routes")
async def list_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods
        })
    return routes

# Add authentication dependency to protected routes
# You can add this to specific routes that need authentication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to console
    ]
)

# Create a logger for the app
logger = logging.getLogger("app")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "ScheduleAI API is running"}

@app.get("/api/protected")
async def protected_route(user = Depends(auth_middleware.verify_token)):
    """Example of a protected route"""
    if not user:
        return {"status": "unauthorized"}
    return {"status": "authenticated", "user": user} 