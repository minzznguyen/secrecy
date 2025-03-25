import os
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Path to the service account key file
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')

# Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service(impersonate_email=None):
    """
    Get an authenticated Google Calendar service
    
    Args:
        impersonate_email (str, optional): Email to impersonate (for domain-wide delegation)
        
    Returns:
        googleapiclient.discovery.Resource: Authenticated Calendar service
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        # If impersonating a user (domain-wide delegation)
        if impersonate_email:
            credentials = credentials.with_subject(impersonate_email)
        
        service = build('calendar', 'v3', credentials=credentials)
        return service
    
    except Exception as e:
        logger.error(f"Error creating calendar service: {str(e)}")
        raise 