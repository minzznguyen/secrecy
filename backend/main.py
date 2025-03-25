from fastapi import FastAPI, Depends, HTTPException
from app.models.meeting import AudioRequest
from pydantic import BaseModel
from app.controllers.meeting_controller import MeetingController
from app.middleware.cors_middleware import CustomCORSMiddleware
from app.middleware.auth_middleware import get_authenticated_user, get_current_user
from dotenv import load_dotenv
import logging
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import os
from app.routes import twilio_routes, calendar_routes
from app.utils.call_manager import CallManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Meeting Scheduler API")

# Add our custom CORS middleware
app.add_middleware(CustomCORSMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get controllers
def get_meeting_controller():
    return MeetingController()

# Define the request model for Eleven Labs conversation
class ElevenLabsRequest(BaseModel):
    text_input: str = None

class ConversationRequest(BaseModel):
    conversationId: str

# Make sure the CallManager is initialized when the app starts
app.state.call_manager = CallManager()

@app.get("/")
def read_root():
    return {"message": "Meeting Scheduler API is running"}

@app.get("/api/hello")
def hello_world():
    return {"message": "Hello from FastAPI!", "status": "success"}

@app.post("/api/meetings")
def create_meeting(
    meeting: dict, 
    user = Depends(get_authenticated_user),
    controller: MeetingController = Depends(get_meeting_controller)
):
    # Add the user ID to the meeting data
    meeting['userId'] = user['uid']
    
    return {
        "message": "Meeting scheduled successfully", 
        "meeting": controller.meeting_service.create_meeting(meeting)
    }

@app.get("/api/meetings")
def get_meetings(controller: MeetingController = Depends(get_meeting_controller)):
    return {"meetings": controller.get_all_meetings()}

@app.get("/api/meeting-example")
def get_meeting_example(controller: MeetingController = Depends(get_meeting_controller)):
    return controller.get_meeting_example()

@app.post("/api/process-audio")
async def process_audio(request: AudioRequest, controller: MeetingController = Depends(get_meeting_controller)):
    return await controller.process_audio(
        request.audioUrl,
        user_id=request.userId,
        client_id=request.clientId,
        meeting_id=request.meetingId
    )

@app.options("/api/test-cors")
async def test_cors_options():
    return {"message": "CORS preflight request successful"}

@app.get("/api/test-cors")
async def test_cors():
    return {"message": "CORS is working!"}

@app.get("/api/cors-test")
async def cors_test():
    """Simple endpoint to test if CORS is working"""
    logger.info("CORS test endpoint called")
    return {
        "message": "CORS is working correctly!",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/process-conversation")
async def process_conversation(request: ConversationRequest, controller: MeetingController = Depends(get_meeting_controller)):
    """Process a conversation and extract meeting details"""
    try:
        logger.info(f"Processing conversation: {request.conversationId}")
        meeting_data = await controller.process_conversation_by_id(request.conversationId)
        return meeting_data
    except Exception as e:
        logger.error(f"Error processing conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/example")
def get_example():
    """Get an example meeting"""
    meeting_controller = get_meeting_controller()
    return meeting_controller.get_meeting_example()

@app.get("/api/get-signed-url")
async def get_signed_url(controller: MeetingController = Depends(get_meeting_controller)):
    """Get a signed URL for connecting to the Eleven Labs agent"""
    return await controller.elevenlabs_controller.get_signed_url()

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, controller: MeetingController = Depends(get_meeting_controller)):
    """Get details of a conversation by ID"""
    return await controller.elevenlabs_controller.get_conversation_details(conversation_id)

@app.post("/api/process-conversation-by-id")
async def process_conversation_by_id(request: dict, controller: MeetingController = Depends(get_meeting_controller)):
    """Process a conversation by ID"""
    conversation_id = request.get("conversation_id")
    if not conversation_id:
        raise HTTPException(status_code=400, detail="Missing conversation_id in request")
    return await controller.process_conversation_by_id(conversation_id)

@app.post("/api/process-text")
async def process_text(request: ElevenLabsRequest, controller: MeetingController = Depends(get_meeting_controller)):
    """Process text input and extract meeting details"""
    try:
        logger.info(f"Processing text input: {request.text_input[:100]}...")
        result = await controller.process_elevenlabs_conversation(request.text_input)
        return result
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add this line after your other app.include_router calls
app.include_router(twilio_routes.router)
app.include_router(calendar_routes.router, prefix="/api", tags=["calendar"])

