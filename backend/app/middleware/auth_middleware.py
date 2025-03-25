import logging
from fastapi import Request, HTTPException, Depends
from firebase_admin import auth, credentials, initialize_app
import firebase_admin
import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK (optional)
firebase_initialized = False
try:
    service_account_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
    
    if os.path.exists(service_account_path):
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
        firebase_initialized = True
        logger.info("Firebase Admin SDK initialized successfully")
    else:
        logger.warning(f"Service account key file not found at: {service_account_path}. Firebase authentication will be disabled.")
except Exception as e:
    logger.warning(f"Error initializing Firebase Admin SDK: {str(e)}. Firebase authentication will be disabled.")

async def verify_token(request: Request):
    """
    Verify Firebase ID token in the Authorization header
    """
    if not firebase_initialized:
        # Skip authentication if Firebase is not initialized
        return None
    
    # Skip token verification for certain paths
    if request.url.path in ['/api/health', '/api/twilio/voice', '/api/twilio/status', '/api/twilio/media-stream']:
        return None
    
    # Get the Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    # Extract the token
    token = auth_header.split('Bearer ')[1]
    
    try:
        # Verify the token
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return None

async def get_current_user(request: Request):
    """Get the current user from the Firebase ID token"""
    authorization = request.headers.get("Authorization")
    
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        logger.error(f"Error verifying Firebase ID token: {str(e)}")
        return None

async def get_authenticated_user(request: Request):
    """Get the authenticated user or raise an exception"""
    user = await get_current_user(request)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    return user 