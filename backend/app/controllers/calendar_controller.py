import logging
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional

from app.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

class CalendarController:
    """Controller for calendar operations, wrapping the existing calendar service"""
    
    def __init__(self, calendar_service: CalendarService):
        self.calendar_service = calendar_service
        logger.info("CalendarController initialized")
    
    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a calendar event"""
        try:
            logger.info(f"Creating calendar event with data: {event_data}")
            result = await self.calendar_service.create_event(event_data)
            logger.info(f"Calendar event created: {result}")
            return result
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise

    async def create_event_with_host(self, meeting_details: Dict[str, Any], 
                                    host_email: str, 
                                    host_availability: Optional[str] = None) -> Dict[str, Any]:
        """Create a calendar event with the host as an attendee"""
        try:
            logger.info(f"Creating calendar event with host data:")
            logger.info(f"Meeting details: {meeting_details}")
            logger.info(f"Host email: {host_email}")
            logger.info(f"Host availability: {host_availability}")
            
            # Process the meeting times
            start_time = meeting_details.get('start_time')
            end_time = meeting_details.get('end_time')
            
            # Convert text times to datetime objects if needed
            start_datetime, end_datetime = self._process_meeting_times(start_time, end_time)
            
            # Create the event data
            event_data = {
                'summary': meeting_details.get('title', 'Scheduled Meeting'),
                'location': meeting_details.get('location', ''),
                'description': meeting_details.get('description', ''),
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # Default timezone
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # Default timezone
                },
                'attendees': [
                    {'email': host_email}
                ],
                'reminders': {
                    'useDefault': True
                }
            }
            
            # Create the event using the calendar service
            result = await self.calendar_service.create_event(event_data)
            logger.info(f"Calendar event created with host: {result}")
            return result
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise
    
    def _process_meeting_times(self, start_time, end_time):
        """Process meeting times from text to datetime objects"""
        logger.info(f"Processing meeting times: {start_time} to {end_time}")
        
        # Default to current time + 1 hour for start, and +2 hours for end
        now = datetime.now()
        default_start = now + timedelta(hours=1)
        default_end = now + timedelta(hours=2)
        
        try:
            # If start_time and end_time are already datetime objects
            if isinstance(start_time, datetime) and isinstance(end_time, datetime):
                return start_time, end_time
            
            # Try to parse as ISO format strings
            if isinstance(start_time, str) and isinstance(end_time, str):
                try:
                    start_datetime = datetime.fromisoformat(start_time)
                    end_datetime = datetime.fromisoformat(end_time)
                    return start_datetime, end_datetime
                except ValueError:
                    # Not ISO format, continue to other parsing methods
                    pass
            
            # If start_time and end_time are strings (natural language), 
            # we need to parse them - this is a simple implementation
            if isinstance(start_time, str) and start_time:
                # For this example, we'll use a very basic parser
                # In a real implementation, you'd want to use a more robust
                # natural language date parser like dateparser
                
                # Example: "3 p.m. next Monday"
                if "next monday" in start_time.lower():
                    # Calculate next Monday
                    days_until_next_monday = (7 - now.weekday()) % 7
                    if days_until_next_monday == 0:
                        days_until_next_monday = 7  # If today is Monday, get next Monday
                    
                    next_monday = now + timedelta(days=days_until_next_monday)
                    
                    # Set time to 3 PM if "3 p.m." is in the string
                    if "3 p.m." in start_time or "3 pm" in start_time.lower():
                        start_datetime = next_monday.replace(hour=15, minute=0, second=0, microsecond=0)
                    else:
                        # Default to noon
                        start_datetime = next_monday.replace(hour=12, minute=0, second=0, microsecond=0)
                else:
                    # Default to tomorrow at noon
                    tomorrow = now + timedelta(days=1)
                    start_datetime = tomorrow.replace(hour=12, minute=0, second=0, microsecond=0)
            else:
                start_datetime = default_start
            
            # Similar logic for end_time
            if isinstance(end_time, str) and end_time:
                if "next monday" in end_time.lower():
                    days_until_next_monday = (7 - now.weekday()) % 7
                    if days_until_next_monday == 0:
                        days_until_next_monday = 7
                    
                    next_monday = now + timedelta(days=days_until_next_monday)
                    
                    if "4 p.m." in end_time or "4 pm" in end_time.lower():
                        end_datetime = next_monday.replace(hour=16, minute=0, second=0, microsecond=0)
                    else:
                        # Default to 1 hour after start time
                        end_datetime = start_datetime + timedelta(hours=1)
                else:
                    # Default to 1 hour after start time
                    end_datetime = start_datetime + timedelta(hours=1)
            else:
                end_datetime = start_datetime + timedelta(hours=1)
            
            logger.info(f"Processed times: {start_datetime} to {end_datetime}")
            return start_datetime, end_datetime
            
        except Exception as e:
            logger.error(f"Error processing meeting times: {str(e)}")
            logger.info(f"Using default times")
            return default_start, default_end 