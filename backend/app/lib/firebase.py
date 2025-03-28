import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase Admin SDK with Firestore"""
    try:
        # Try to get the app if it's already initialized
        firebase_admin.get_app()
        logger.info("Firebase Admin SDK already initialized")
    except ValueError:
        # If not initialized, initialize it
        service_account_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
        
        if not service_account_path:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY_PATH environment variable not set")
        
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account key file not found at: {service_account_path}")
        
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully") 