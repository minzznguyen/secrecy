from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI):
    """Configure CORS for the application"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],  # Vite's default port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 