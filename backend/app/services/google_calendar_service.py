from datetime import datetime
import pytz
from typing import Dict, Optional, Tuple
import requests
from fastapi import HTTPException
import re
import aiohttp

class GoogleCalendarService:
    def __init__(self):
        self.CALENDAR_API_BASE_URL = 'https://www.googleapis.com/calendar/v3'
        # ISO 8601 format regex pattern
        self.iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

    def ensure_iso_format(self, date_string: str) -> str:
        """Ensure date string is in ISO format"""
        try:
            if not date_string or not isinstance(date_string, str):
                raise ValueError("Date string is required and must be a string")
                
            # If it's already in ISO format, just ensure it has timezone
            if self.iso_pattern.match(date_string):
                # Add UTC timezone if no timezone specified
                if date_string.endswith('Z'):
                    return date_string
                elif '+' in date_string or '-' in date_string[-6:]:
                    return date_string
                else:
                    return date_string + 'Z'
            
            # Try to parse the date string
            date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date.isoformat() + 'Z'  # Ensure UTC timezone
            
        except Exception as e:
            print(f"Error formatting date: {str(e)}")
            raise ValueError(f"Invalid date format: {date_string}")

    def get_local_timezone(self) -> str:
        """Get the local timezone as an IANA timezone identifier"""
        try:
            # Get the local timezone
            local_tz = datetime.now().astimezone().tzinfo
            
            # If it's a zoneinfo timezone (Python 3.9+), use its key
            if hasattr(local_tz, 'key'):
                return local_tz.key
            
            # For pytz timezones, use the zone name
            if hasattr(local_tz, 'zone'):
                return local_tz.zone
            
            # Fallback to UTC if we can't determine the timezone
            return 'UTC'
        except Exception as e:
            print(f"Error getting timezone: {str(e)}")
            return 'UTC'

    def format_meeting_for_calendar(self, meeting_data: Dict) -> Dict:
        """Format meeting data for Google Calendar API"""
        try:
            if not isinstance(meeting_data, dict):
                raise ValueError("Meeting data must be a dictionary")
                
            start_time = meeting_data.get("startDateTime")
            end_time = meeting_data.get("endDateTime")
            
            if not start_time or not end_time:
                raise ValueError("Start and end times are required")
            
            # Get IANA timezone identifier
            timezone = self.get_local_timezone()
            print(f"Using timezone: {timezone}")
            
            return {
                "summary": meeting_data.get("title", ""),
                "description": meeting_data.get("description", ""),
                "start": {
                    "dateTime": self.ensure_iso_format(start_time),
                    "timeZone": timezone
                },
                "end": {
                    "dateTime": self.ensure_iso_format(end_time),
                    "timeZone": timezone
                }
            }
        except Exception as e:
            print(f"Error formatting meeting data: {str(e)}")
            raise ValueError(f"Invalid meeting data format: {str(e)}")

    async def test_calendar_access(self, access_token: str) -> Dict:
        """Test if the token has calendar permissions"""
        try:
            print("Testing calendar access with token")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.CALENDAR_API_BASE_URL}/users/me/calendarList",
                    headers={"Authorization": f"Bearer {access_token}"}
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        print(f"Calendar API test failed: {error_text}")
                        return {
                            "success": False,
                            "error": f"Status: {response.status}, Details: {error_text}"
                        }
                    
                    data = await response.json()
                    return {
                        "success": True,
                        "calendars": len(data.get("items", [])),
                        "primaryCalendarId": next(
                            (cal["id"] for cal in data.get("items", []) if cal.get("primary")),
                            "primary"
                        )
                    }
        except Exception as e:
            print(f"Error testing calendar access: {str(e)}")
            return {"success": False, "error": str(e)}

    async def create_event(
        self,
        access_token: str,
        calendar_id: str = "primary",
        event_data: Optional[Dict] = None
    ) -> Dict:
        """Create a new event in the user's calendar"""
        try:
            print(f"Creating calendar event with token: {access_token[:10]}...")
            print(f"Calendar ID: {calendar_id}")
            print(f"Event data: {event_data}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.CALENDAR_API_BASE_URL}/calendars/{calendar_id}/events",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json=event_data
                ) as response:
                    if not response.ok:
                        error_text = await response.text()
                        print(f"Calendar API error response: {error_text}")
                        raise HTTPException(
                            status_code=response.status,
                            detail=f"Failed to create event: {error_text}"
                        )
                    
                    return await response.json()
        except Exception as e:
            print(f"Error creating event: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error creating calendar event: {str(e)}"
            )

    async def create_event_with_refresh(
        self,
        access_token: str,
        refresh_token: str,
        calendar_id: str,
        event_data: Dict
    ) -> Dict:
        """Create an event with token refresh capability"""
        try:
            # First attempt with current token
            try:
                return await self.create_event(access_token, calendar_id, event_data)
            except HTTPException as e:
                # If unauthorized, try to refresh token
                if e.status_code == 401:
                    if not refresh_token:
                        raise ValueError("No refresh token available")
                    
                    # Here you would typically call your token refresh endpoint
                    # For now, we'll raise an error to handle it in the route
                    raise HTTPException(
                        status_code=401,
                        detail="Token expired and needs refresh"
                    )
                raise e
        except Exception as e:
            print(f"Error creating event with refresh: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error creating calendar event: {str(e)}"
            )