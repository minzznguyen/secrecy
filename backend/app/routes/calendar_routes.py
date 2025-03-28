from fastapi import APIRouter, Depends, HTTPException
from ..controllers.calendar_controller import CalendarController
from ..middleware.auth_middleware import get_authenticated_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["calendar"])

def get_calendar_controller():
    return CalendarController()

@router.post("/create-event")
async def create_event(
    request: dict,
    user = Depends(get_authenticated_user),
    controller: CalendarController = Depends(get_calendar_controller)
):
    """
    Create a calendar event using the user's stored Google tokens
    
    Request body:
    {
        "user_id": "string",
        "meeting_data": {
            "title": "string",
            "startDateTime": "string",
            "endDateTime": "string",
            "description": "string"
        }
    }
    """
    try:
        # Extract meeting data from request
        meeting_data = request.get("meeting_data")
        if not meeting_data:
            raise HTTPException(status_code=400, detail="No meeting data provided")
        
        # Create the event
        event = await controller.create_event(user["uid"], meeting_data)
        
        return {
            "success": True,
            "event_id": event.get("id"),
            "event": event
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creating calendar event: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create calendar event: {str(e)}"
        ) 