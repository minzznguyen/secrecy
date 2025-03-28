import logging
import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from datetime import datetime

logger = logging.getLogger(__name__)

load_dotenv()

class FirebaseService:
    def __init__(self):
        # Initialize Firebase Admin SDK if not already initialized
        if not firebase_admin._apps:
            cred = credentials.Certificate({
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
            })
            firebase_admin.initialize_app(cred)
        
        self.db = firestore.client()
        print("FirebaseService initialized with Firestore")
    
    async def get_user_tokens(self, user_email: str) -> Optional[Dict]:
        """Get user's Google tokens from Firestore"""
        try:
            print(f"Getting tokens for user: {user_email}")
            # Get the document directly using email as document ID
            doc_ref = self.db.collection('user_tokens').document(user_email)
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"No tokens found for user: {user_email}")
                return None
            
            token_data = doc.to_dict()
            print(f"Found tokens for user: {user_email}")
            return token_data
            
        except Exception as e:
            print(f"Error getting user tokens: {str(e)}")
            return None
    
    async def store_user_tokens(self, user_email: str, tokens: Dict) -> bool:
        """Store user's Google tokens in Firestore"""
        try:
            print(f"Storing tokens for user: {user_email}")
            
            # Store directly using email as document ID
            doc_ref = self.db.collection('user_tokens').document(user_email)
            doc_ref.set(tokens, merge=True)
            print(f"Stored tokens for user: {user_email}")
            
            return True
            
        except Exception as e:
            print(f"Error storing user tokens: {str(e)}")
            return False 