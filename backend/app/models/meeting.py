from pydantic import BaseModel
from typing import List, Optional

class AudioRequest(BaseModel):
    audioUrl: str
    userId: Optional[str] = None
    clientId: Optional[str] = None
    meetingId: Optional[str] = None

class Attendee(BaseModel):
    name: str
    email: Optional[str] = None

class MeetingSchedule(BaseModel):
    title: str
    description: Optional[str] = None
    startDateTime: str
    endDateTime: str
    location: Optional[str] = None
    attendees: Optional[List[Attendee]] = []
    organizer: Optional[str] = None
    timezone: Optional[str] = None 