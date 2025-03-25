from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from ..controllers.calendar_controller import CalendarController
from ..dependencies import get_calendar_controller

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/test-calendar")
async def test_calendar_integration(data: Dict[str, Any], 
                                    calendar_controller: CalendarController = Depends(get_calendar_controller)):
    """Test endpoint for calendar integration with dummy data"""
    logger.info("Testing calendar integration with dummy data")
    
    try:
        meeting_details = data.get("meeting_details", {})
        host_email = data.get("host_email", "")
        host_availability = data.get("host_availability", "")
        
        logger.info(f"Received test data: {meeting_details}")
        logger.info(f"Host email: {host_email}")
        logger.info(f"Host availability: {host_availability}")
        
        # Validate required data
        if not meeting_details or not host_email:
            raise HTTPException(status_code=400, detail="Missing required data")
        
        # Create the event using the calendar controller
        result = await calendar_controller.create_event_with_host(
            meeting_details,
            host_email,
            host_availability
        )
        
        logger.info(f"Test calendar integration result: {result}")
        
        return {
            "success": result.get("success", False),
            "event": result,
            "message": "Calendar integration test completed"
        }
    
    except Exception as e:
        logger.error(f"Error in calendar integration test: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Calendar integration test failed"
        } 