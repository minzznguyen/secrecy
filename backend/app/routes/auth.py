from fastapi import APIRouter, HTTPException
from firebase_admin import auth
from google.oauth2 import id_token
from google.auth.transport import requests
from pydantic import BaseModel
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

class TokenRequest(BaseModel):
    access_token: str

@router.post("/create-custom-token")
async def create_custom_token(request: TokenRequest):
    try:
        logger.info("Received request to create custom token")
        logger.info(f"Client ID: {os.getenv('GOOGLE_CLIENT_ID')}")
        
        # Verify the Google access token
        logger.info("Verifying Google access token...")
        idinfo = id_token.verify_oauth2_token(
            request.access_token, 
            requests.Request(), 
            os.getenv('GOOGLE_CLIENT_ID')
        )
        
        # Get the user's email from the token
        email = idinfo['email']
        logger.info(f"Token verified for email: {email}")
        
        # Create a custom token for Firebase
        logger.info("Creating Firebase custom token...")
        custom_token = auth.create_custom_token(email)
        logger.info("Firebase custom token created successfully")
        
        return {
            "customToken": custom_token.decode(),
            "email": email,
            "idToken": request.access_token  # Return the Google access token as well
        }
    except Exception as e:
        logger.error(f"Error creating custom token: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 