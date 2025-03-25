import logging
import json
from ..controllers.text_parser_controller import TextParserController
from ..controllers.calendar_controller import CalendarController

logger = logging.getLogger(__name__)

class TranscriptProcessor:
    """Processes call transcripts to extract meeting info and create calendar events"""
    
    def __init__(self, text_parser=None, calendar_controller=None):
        self.text_parser = text_parser or TextParserController()
        self.calendar_controller = calendar_controller or CalendarController()
        logger.info("TranscriptProcessor initialized")
    
    async def process_transcript(self, transcript, call_data):
        """
        Process a transcript from a completed call
        
        Args:
            transcript (str): The formatted call transcript
            call_data (dict): Additional call data
            
        Returns:
            dict: Results of processing
        """
        logger.info("=== TRANSCRIPT PROCESSOR: STARTING PROCESSING ===")
        logger.info(f"Processing transcript with length: {len(transcript)}")
        
        # Extract call metadata
        host_availability = call_data.get("host_availability")
        host_email = call_data.get("host_email")
        host_name = call_data.get("host_name", "Unknown Host")
        conversation_id = call_data.get("conversation_id")
        
        logger.info(f"Call metadata - Host: {host_name}, Email: {host_email}")
        logger.info(f"Conversation ID: {conversation_id}")
        
        try:
            # Step 1: Parse the transcript
            logger.info("Parsing transcript to extract meeting details")
            meeting_details = self.text_parser.parse_to_json(
                transcript, 
                host_availability,
                host_name
            )
            
            if not meeting_details:
                logger.warning("No meeting details could be extracted from transcript")
                return {
                    "success": False,
                    "error": "No meeting details could be extracted"
                }
            
            logger.info(f"Extracted meeting details: {json.dumps(meeting_details, indent=2)}")
            
            # Step 2: Create calendar event
            if meeting_details.get("start_time") or meeting_details.get("startDateTime"):
                logger.info("Creating calendar event with extracted meeting details")
                
                event_result = await self.calendar_controller.create_event_with_host(
                    meeting_details,
                    host_email,
                    host_availability,
                    host_name
                )
                
                logger.info(f"Calendar event created: {event_result.get('id')}")
                
                return {
                    "success": True,
                    "meeting_details": meeting_details,
                    "event": event_result
                }
            else:
                logger.warning("Meeting details missing start time - cannot create calendar event")
                return {
                    "success": False,
                    "meeting_details": meeting_details,
                    "error": "Missing start time"
                }
                
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "error": str(e)
            } 