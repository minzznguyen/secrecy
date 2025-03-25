import logging
from typing import List, Dict, Any
import os
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeetingService:
    def __init__(self):
        # In-memory storage for meetings
        # In a real app, this would be a database
        self.meetings = []
        self.client = OpenAI()  # Automatically reads API key from env
        logger.info("MeetingService initialized")
    
    def create_meeting(self, meeting_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new meeting"""
        self.meetings.append(meeting_data)
        logger.info(f"Meeting created: {meeting_data.get('title', 'Untitled')}")
        return meeting_data
    
    def get_all_meetings(self) -> List[Dict[str, Any]]:
        """Get all meetings"""
        return self.meetings
    
    def get_meeting_by_id(self, meeting_id: str) -> Dict[str, Any]:
        """Get a meeting by ID"""
        # In a real app, you would search by ID
        # For now, we'll just return the first meeting
        return self.meetings[0] if self.meetings else None 