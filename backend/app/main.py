from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from .routes import twilio_routes, calendar_routes
from .middleware import auth_middleware
import logging

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(twilio_routes.router)
app.include_router(calendar_routes.router)

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
    return {"message": "Hello World"}

@app.get("/api/protected")
async def protected_route(user = Depends(auth_middleware.verify_token)):
    """Example of a protected route"""
    if not user:
        return {"status": "unauthorized"}
    return {"status": "authenticated", "user": user} 