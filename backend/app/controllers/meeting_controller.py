import logging
from fastapi import HTTPException
from ..services.meeting_service import MeetingService
from ..controllers.audio_controller import AudioController
from ..controllers.text_parser_controller import TextParserController
from ..controllers.elevenlabs_controller import ElevenLabsController
from openai import OpenAI
import os
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MeetingController:
    def __init__(self):
        self.meeting_service = MeetingService()
        self.audio_controller = AudioController()
        self.text_parser = TextParserController()
        self.elevenlabs_controller = ElevenLabsController()
        self.client = OpenAI()  # Automatically reads API key from env
        logger.info("MeetingController initialized")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    async def process_audio(self, audio_url, user_id=None, client_id=None, meeting_id=None):
        """Process audio and extract meeting details"""
        try:
            # Download audio
            audio_content = await self.audio_controller.download_audio(audio_url)
            
            # Transcribe audio
            transcript = await self.audio_controller.transcribe_audio(audio_content)
            
            # Parse transcript
            parser_result = self.text_parser.parse_to_json(transcript)
            
            # Check if parsing was successful
            if isinstance(parser_result, tuple):
                error_response, status_code = parser_result
                raise HTTPException(status_code=status_code, detail=error_response.get('error', 'Failed to parse transcript'))
            
            # Create meeting
            meeting_data = parser_result.get('formData', {})
            
            # Add metadata if provided
            if user_id:
                meeting_data['userId'] = user_id
            if client_id:
                meeting_data['clientId'] = client_id
            if meeting_id:
                meeting_data['meetingId'] = meeting_id
            
            # Save meeting
            self.meeting_service.create_meeting(meeting_data)
            
            return {
                "status": "success",
                "message": "Audio processed successfully",
                "transcript": transcript,
                "meeting": meeting_data
            }
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
    
    async def process_elevenlabs_conversation(self, text_input=None):
        """Process a conversation with Eleven Labs agent and extract meeting details"""
        try:
            # Use the transcript directly from the frontend
            transcript = text_input
            
            logger.info(f"Processing transcript from frontend: {transcript[:100]}...")
            
            # Parse transcript using the text parser controller
            parser_result = self.text_parser.parse_to_json(transcript)
            
            # Check if parsing was successful
            if isinstance(parser_result, tuple):
                error_response, status_code = parser_result
                raise HTTPException(status_code=status_code, detail=error_response.get('error', 'Failed to parse transcript'))
            
            # Create meeting
            meeting_data = parser_result.get('formData', {})
            
            # Save meeting
            self.meeting_service.create_meeting(meeting_data)
            
            return {
                "status": "success",
                "message": "Conversation processed successfully",
                "transcript": transcript,
                "meeting": meeting_data
            }
        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error processing conversation: {str(e)}")
    
    async def process_conversation_by_id(self, conversation_id):
        """Process a conversation by ID"""
        try:
            logger.info(f"Processing conversation by ID: {conversation_id}")
            
            # Get conversation details from Eleven Labs API
            conversation_details = await self.elevenlabs_controller.get_conversation_details(conversation_id)
            
            # Extract the transcript
            transcript = ""
            if "messages" in conversation_details:
                for message in conversation_details["messages"]:
                    role = "Assistant" if message.get("source") == "agent" else "User"
                    transcript += f"{role}: {message.get('message', '')}\n"
            
            logger.info(f"Extracted transcript: {transcript[:200]}...")
            
            # Use the existing text parser to extract meeting details
            parser_result = self.text_parser.parse_to_json(transcript)
            
            # Check if parsing was successful
            if isinstance(parser_result, tuple):
                error_response, status_code = parser_result
                raise HTTPException(status_code=status_code, detail=error_response.get('error', 'Failed to parse transcript'))
            
            # Create meeting
            meeting_data = parser_result.get('formData', {})
            
            # Save meeting
            self.meeting_service.create_meeting(meeting_data)
            
            return meeting_data
            
        except Exception as e:
            logger.error(f"Error processing conversation: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def extract_meeting_details(self, transcript):
        """Extract meeting details from transcript using OpenAI"""
        try:
            prompt = f"""
            Extract meeting details from the following conversation transcript.
            Return a JSON object with the following fields:
            - title: The title or subject of the meeting
            - startDateTime: The start date and time in ISO format (or null if not specified)
            - endDateTime: The end date and time in ISO format (or null if not specified)
            - description: A brief description of the meeting purpose
            
            Transcript:
            {transcript}
            
            JSON:
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts meeting details from conversations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            
            # Parse the JSON response
            try:
                meeting_data = json.loads(result)
                logger.info(f"Successfully extracted meeting data: {meeting_data}")
                return meeting_data
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON from OpenAI response: {result}")
                # Attempt to extract JSON from the response text
                import re
                json_match = re.search(r'```json\n(.*?)\n```', result, re.DOTALL)
                if json_match:
                    try:
                        meeting_data = json.loads(json_match.group(1))
                        return meeting_data
                    except:
                        pass
                
                # Return a basic structure if parsing fails
                return {
                    "title": "Meeting",
                    "startDateTime": None,
                    "endDateTime": None,
                    "description": "Meeting details could not be extracted."
                }
                
        except Exception as e:
            logger.error(f"Error extracting meeting details: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_all_meetings(self):
        """Get all meetings"""
        return self.meeting_service.get_all_meetings()
    
    def get_meeting_example(self):
        """Get example meeting"""
        import os
        import json
        
        schema_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas")
        with open(os.path.join(schema_dir, "meetingExample.json"), "r") as f:
            example_meeting = json.load(f)
        
        return example_meeting 