import logging
import os
import aiohttp
from ..services.google_calendar_service import GoogleCalendarService
from ..services.firebase_service import FirebaseService
from fastapi import HTTPException
from datetime import datetime
from firebase_admin import auth

logger = logging.getLogger(__name__)

class CalendarController:
    def __init__(self):
        self.calendar_service = GoogleCalendarService()
        self.firebase_service = FirebaseService()
        self.google_token_url = 'https://oauth2.googleapis.com/token'
        logger.info("Calendar Controller initialized")
    
    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Get a new access token using the refresh token
        
        Args:
            refresh_token (str): The refresh token to use
            
        Returns:
            dict: New token information including access_token
        """
        try:
            # Prepare the token refresh request
            data = {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            logger.info("Attempting to refresh access token")
            
            # Make the request to Google's token endpoint using aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(self.google_token_url, data=data) as response:
                    if not response.ok:
                        error_text = await response.text()
                        logger.error(f"Token refresh failed: {error_text}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Failed to refresh token: {error_text}"
                        )
                    
                    token_data = await response.json()
                    
                    # Update the tokens in Firebase with new access token
                    updated_tokens = {
                        'access_token': token_data['access_token'],
                        'token_expiry': datetime.now().timestamp() + token_data['expires_in'],
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    logger.info("Successfully refreshed access token")
                    return updated_tokens
            
        except Exception as e:
            logger.error(f"Error refreshing access token: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh access token: {str(e)}"
            )
    
    async def create_event(self, user_id: str, meeting_data: dict) -> dict:
        """
        Create a calendar event using the user's stored tokens
        
        Args:
            user_id (str): The Firebase user ID
            meeting_data (dict): The meeting data to create
            
        Returns:
            dict: The created event data
        """
        try:
            # Get user's email from Firebase Auth
            user = auth.get_user(user_id)
            user_email = user.email
            
            if not user_email:
                raise HTTPException(
                    status_code=400,
                    detail="User email not found"
                )
            
            # Get user's tokens from Firebase using email
            tokens = await self.firebase_service.get_user_tokens(user_email)
            
            if not tokens:
                raise HTTPException(
                    status_code=401,
                    detail="No Google tokens found. Please authenticate with Google first."
                )
            
            logger.info(f"Retrieved tokens for user {user_email}")
            
            # Check if we need to refresh the access token
            current_time = datetime.now().timestamp()
            token_expiry = float(tokens.get('token_expiry', 0))
            
            if current_time >= token_expiry:
                logger.info("Access token expired, refreshing...")
                # Get new access token
                updated_tokens = await self.refresh_access_token(tokens['refresh_token'])
                
                # Update the stored tokens
                tokens.update(updated_tokens)
                await self.firebase_service.store_user_tokens(user_email, tokens)
                
                logger.info("Successfully refreshed and stored new access token")
            
            # Format the meeting data for Google Calendar
            formatted_event = self.calendar_service.format_meeting_for_calendar(meeting_data)
            
            # Create the event using the current/refreshed access token
            event = await self.calendar_service.create_event(
                access_token=tokens['access_token'],
                calendar_id='primary',
                event_data=formatted_event
            )
            
            logger.info(f"Successfully created calendar event for user {user_email}")
            return event
            
        except Exception as e:
            logger.error(f"Error creating calendar event for user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create calendar event: {str(e)}"
            ) 