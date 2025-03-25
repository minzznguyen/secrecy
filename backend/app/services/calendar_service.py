import logging
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from ..utils.google_service_account import get_calendar_service
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class CalendarService:
    """Service for interacting with Google Calendar API"""
    
    def __init__(self):
        """Initialize the Google Calendar service"""
        try:
            # Get the service account key file path
            key_file = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY_FILE", "serviceAccountKeys.json")
            
            # Load the service account credentials
            logger.info(f"Loading service account credentials from {key_file}")
            self.credentials = service_account.Credentials.from_service_account_file(
                key_file,
                scopes=["https://www.googleapis.com/auth/calendar"]
            )
            
            # Build the calendar service
            self.service = build("calendar", "v3", credentials=self.credentials)
            logger.info("Calendar service initialized successfully")
            
            # Get the calendar ID (default is primary)
            self.calendar_id = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
            logger.info(f"Using calendar ID: {self.calendar_id}")
            
        except Exception as e:
            logger.error(f"Error initializing calendar service: {str(e)}")
            raise
    
    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event"""
        try:
            logger.info(f"Creating calendar event with data: {json.dumps(event_data, indent=2)}")
            
            # Add the Calendar ID to event data
            event_data = {**event_data, "calendarId": self.calendar_id}
            
            # Set sendUpdates to 'all' to notify attendees
            event_data["sendUpdates"] = "all"
            
            # Create the event in Google Calendar
            event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event_data,
                sendUpdates="all"
            ).execute()
            
            logger.info(f"Event created: {event.get('htmlLink')}")
            
            return {
                "success": True,
                "event_id": event.get("id"),
                "html_link": event.get("htmlLink"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end"),
                "attendees": event.get("attendees")
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            error_details = str(e)
            
            # Return error information
            return {
                "success": False,
                "error": "Failed to create calendar event",
                "error_details": error_details
            }
    
    async def create_event_with_attendee(self, event_data, host_email, host_availability=None):
        """
        Create a calendar event and invite the host as an attendee
        
        Args:
            event_data (dict): Event data including summary, description, start, end
            host_email (str): Email address of the host to invite
            host_availability (str, optional): Host's availability constraints
            
        Returns:
            dict: Created event details
        """
        logger.info(f"Creating calendar event with host {host_email}: {event_data}")
        
        try:
            # Enhance the description with host availability if provided
            description = event_data.get("description", "")
            if host_availability:
                description += f"\n\nHost's weekly availability: {host_availability}"
            
            # Update the event data with the enhanced description
            event_data["description"] = description
            
            # For testing, we'll use the mock implementation
            # In production, uncomment the real implementation below
            
            # Mock implementation
            event_id = f"event_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"Created mock event with ID: {event_id} and invited {host_email}")
            
            # Return a mock response
            return {
                "id": event_id,
                "summary": event_data.get("summary"),
                "description": description,  # Use the enhanced description
                "start": event_data.get("start"),
                "end": event_data.get("end"),
                "status": "confirmed",
                "created": datetime.now().isoformat(),
                "attendees": [
                    {"email": host_email, "responseStatus": "needsAction"}
                ]
            }
            
            # Real implementation:
            """
            service = get_calendar_service()
            
            event = {
                "summary": event_data.get("summary"),
                "description": description,  # Use the enhanced description
                "start": {
                    "dateTime": event_data.get("start"),
                    "timeZone": "America/Los_Angeles"
                },
                "end": {
                    "dateTime": event_data.get("end"),
                    "timeZone": "America/Los_Angeles"
                },
                "attendees": [
                    {"email": host_email}
                ]
            }
            
            # sendUpdates='all' ensures notifications are sent to attendees
            created_event = service.events().insert(
                calendarId=self.calendar_id, 
                body=event, 
                sendUpdates='all'
            ).execute()
            
            return created_event
            """
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise 