from fastapi import APIRouter, Request, Response, Depends, HTTPException, WebSocket, WebSocketDisconnect
from ..controllers.twilio_controller import TwilioController
from ..controllers.elevenlabs_controller import ElevenLabsController
from ..controllers.text_parser_controller import TextParserController
from ..utils.twilio_audio_interface import TwilioAudioInterface
from ..utils.call_manager import CallManager
from pydantic import BaseModel
from typing import Optional
import json
import os
import traceback
import urllib.parse
from twilio.twiml.voice_response import VoiceResponse, Connect
import datetime
import time
from ..services.google_calendar_service import GoogleCalendarService
from ..services.firebase_service import FirebaseService

# Try to import from the documented structure
try:
    from elevenlabs import ElevenLabs
    from elevenlabs.conversational_ai.conversation import Conversation
except ImportError:
    # Fallback to newer structure if available
    try:
        from elevenlabs.api import Conversation
        from elevenlabs import Client as ElevenLabsClient
    except ImportError:
        # Fallback imports or error handling
        print("ERROR: Could not import required ElevenLabs modules. Please install the latest version.")
        Conversation = None
        ElevenLabsClient = None

router = APIRouter(prefix="/api/twilio", tags=["twilio"])

# Initialize ElevenLabs client based on available imports
try:
    if 'ElevenLabsClient' in locals() and ElevenLabsClient:
        eleven_labs_client = ElevenLabsClient(api_key=os.getenv("ELEVENLABS_API_KEY"))
    else:
        eleven_labs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
    
    ELEVEN_LABS_AGENT_ID = os.getenv("AGENT_ID")
except NameError:
    print("WARNING: ElevenLabs client could not be initialized.")
    eleven_labs_client = None
    ELEVEN_LABS_AGENT_ID = os.getenv("AGENT_ID")

# Initialize the call manager
call_manager = CallManager()

# Initialize services
firebase_service = FirebaseService()
calendar_service = GoogleCalendarService()

class CallRequest(BaseModel):
    phone_number: str
    host_availability: Optional[str] = None
    host_email: Optional[str] = None
    host_name: Optional[str] = None  # Add host_name field

# Dependencies
def get_twilio_controller():
    return TwilioController()

def get_elevenlabs_controller():
    return ElevenLabsController()

def get_text_parser_controller():
    return TextParserController()

@router.post("/call")
async def initiate_call(
    request: CallRequest,
    controller: TwilioController = Depends(get_twilio_controller)
):
    """Initiate a call to the customer"""
    print("\n=== CALL ENDPOINT: RECEIVED REQUEST ===")
    print(f"Phone Number: '{request.phone_number}'")
    print(f"Host Availability: '{request.host_availability}'")
    print(f"Host Email: '{request.host_email}'")
    print(f"Host Name: '{request.host_name}'")  # Log the name
    print("======================================\n")
    
    result = await controller.initiate_call(
        request.phone_number,
        request.host_availability,
        request.host_email,
        request.host_name  # Pass the name to the controller
    )
    
    # Store the parameters with the call SID
    if result.get("status") == "success" and "call_sid" in result:
        call_manager.store_pending_params(
            result["call_sid"],
            request.host_availability,
            request.host_email,
            request.host_name  # Store the name in pending params
        )
    
    print("\n=== CALL ENDPOINT: RETURNING RESPONSE ===")
    print(f"Response: {result}")
    print("========================================\n")
    
    return result

@router.post("/voice")
async def twilio_voice_webhook(request: Request):
    """
    Webhook for Twilio to get TwiML instructions for the call
    This connects the call to the ElevenLabs agent
    """
    try:
        print("\n=== VOICE WEBHOOK: REQUEST RECEIVED ===")
        # Log the full request for debugging
        form_data = await request.form()
        headers = dict(request.headers)
        query_params = dict(request.query_params)
        print(f"Headers: {headers}")
        print(f"Query params: {query_params}")
        print(f"Form data: {dict(form_data)}")
        print("======================================\n")
        
        # Get parameters from query parameters if present
        availability = request.query_params.get("availability", "")
        host_email = request.query_params.get("host_email", "")
        host_name = request.query_params.get("host_name", "")  # Get host name
        
        print("\n=== VOICE WEBHOOK: EXTRACTED PARAMETERS ===")
        print(f"Availability: '{availability}'")
        print(f"Host Email: '{host_email}'")
        print(f"Host Name: '{host_name}'")  # Log host name
        print("===========================================\n")
        
        # Get the Call SID from the request
        call_sid = form_data.get("CallSid")
        
        print("\n=== VOICE WEBHOOK: CALL SID ===")
        print(f"Call SID: '{call_sid}'")
        print("===============================\n")
        
        # Store the parameters with the Call SID
        if call_sid:
            call_manager.store_call_params(call_sid, {
                "availability": availability,
                "host_email": host_email,
                "host_name": host_name  # Store host name
            })
        
        # Generate TwiML to connect to ElevenLabs
        # Use request.headers.get("host") to get the hostname
        host = request.headers.get("host") or request.url.netloc
        print(f"Using host: {host}")
        
        # Create a properly formatted TwiML response
        twiml = VoiceResponse()
        twiml.say("")
        connect = Connect()
        
        # Build the stream URL with query parameters
        stream_url = f"wss://{host}/api/twilio/media-stream"
        
        # Add parameters to the stream URL
        params = []
        if availability:
            encoded_availability = urllib.parse.quote(availability)
            params.append(f"availability={encoded_availability}")
        if host_email:
            encoded_host_email = urllib.parse.quote(host_email)
            params.append(f"host_email={encoded_host_email}")
        if host_name:
            encoded_host_name = urllib.parse.quote(host_name)
            params.append(f"host_name={encoded_host_name}")  # Add host name
            
        if params:
            stream_url += "?" + "&".join(params)
        
        print("\n=== VOICE WEBHOOK: STREAM URL ===")
        print(f"Stream URL: {stream_url}")
        print("=================================\n")
        
        connect.stream(url=stream_url)
        twiml.append(connect)
        
        # Convert to string and log
        twiml_str = str(twiml)
        print("\n=== VOICE WEBHOOK: GENERATED TWIML ===")
        print(f"TwiML: {twiml_str}")
        print("=====================================\n")
        
        return Response(content=twiml_str, media_type="application/xml")
    except Exception as e:
        print(f"Error in twilio_voice_webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return a simple TwiML response in case of error
        error_twiml = VoiceResponse()
        error_twiml.say("Sorry, there was an error connecting to our scheduling assistant. Please try again later.")
        
        return Response(content=str(error_twiml), media_type="application/xml")

@router.websocket("/media-stream")
async def handle_media_stream(
    websocket: WebSocket,
    elevenlabs_controller: ElevenLabsController = Depends(get_elevenlabs_controller)
):
    """WebSocket endpoint for the media stream between Twilio and ElevenLabs"""
    try:
        await websocket.accept()
        print("\n=== WEBSOCKET: CONNECTION ESTABLISHED ===\n")
        
        # Initialize variables
        availability = ""
        host_email = ""
        host_name = "the host"  # Default name
        stream_sid = None
        conversation = None
        
        # First try to get parameters from query parameters
        query_availability = websocket.query_params.get("availability", "")
        query_host_email = websocket.query_params.get("host_email", "")
        query_host_name = websocket.query_params.get("host_name", "")  # Get host name
        
        print("\n=== WEBSOCKET: QUERY PARAMETERS ===")
        print(f"Query Availability: '{query_availability}'")
        print(f"Query Host Email: '{query_host_email}'")
        print(f"Query Host Name: '{query_host_name}'")  # Log host name
        print("==================================\n")
        
        if query_availability or query_host_email or query_host_name:
            availability = query_availability
            host_email = query_host_email
            if query_host_name:
                host_name = query_host_name  # Use the provided name if available
            
            print(f"\n=== WEBSOCKET: USING PARAMETERS FROM QUERY ===")
            print(f"Availability: '{availability}'")
            print(f"Host Email: '{host_email}'")
            print(f"Host Name: '{host_name}'")  # Log host name
            print(f"===========================================\n")
        
        # Wait for the first message to get the stream SID
        first_message = True
        
        # Print all call manager data for debugging
        print("\n=== WEBSOCKET: CALL MANAGER DATA ===")
        print(f"Active Calls: {call_manager.active_calls}")
        print(f"Call Params: {call_manager.call_params}")
        print(f"Pending Params: {call_manager.pending_params}")
        print("==================================\n")
        
        # Global variable to store the transcript in this function's scope
        full_transcript = []
        
        # Define callbacks for the conversation
        def agent_response_callback(text):
            print(f"\n=== AGENT RESPONSE CALLBACK ===")
            print(f"Text: {text}")
            print(f"===============================\n")
            if stream_sid:
                call_manager.add_transcript_entry(stream_sid, "agent", text)
            # Also store in our local variable
            full_transcript.append({"role": "agent", "content": text})
        
        def user_transcript_callback(text):
            print(f"\n=== USER TRANSCRIPT CALLBACK ===")
            print(f"Text: {text}")
            print(f"===============================\n")
            if stream_sid:
                call_manager.add_transcript_entry(stream_sid, "user", text)
            # Also store in our local variable
            full_transcript.append({"role": "user", "content": text})
        
        async for message in websocket.iter_text():
            if not message:
                continue
                
            try:
                data = json.loads(message)
                
                # Only log non-media events to reduce noise
                if data["event"] != "media":
                    print(f"\n=== WEBSOCKET: RECEIVED MESSAGE FROM TWILIO ===")
                    print(f"Event: {data['event']}")
                    if data["event"] == "start":
                        print(f"Start Data: {data['start']}")
                    print(f"==============================================\n")
                
                # If this is the first message and it's a start event, try to get parameters from call manager
                if first_message and data["event"] == "start" and "streamSid" in data["start"]:
                    first_message = False
                    stream_sid = data["start"]["streamSid"]
                    
                    print(f"\n=== WEBSOCKET: RECEIVED STREAM SID ===")
                    print(f"Stream SID: '{stream_sid}'")
                    print(f"===================================\n")
                    
                    # Try to find the call in the call manager
                    print(f"\n=== WEBSOCKET: SEARCHING CALL MANAGER FOR PARAMETERS ===")
                    for call_sid, call_data in call_manager.active_calls.items():
                        print(f"Checking call SID: '{call_sid}'")
                        print(f"Call data: {call_data}")
                    print(f"=====================================================\n")
                    
                    for call_sid, call_data in call_manager.active_calls.items():
                        # If we find a match, use those parameters
                        if not (availability or host_email or host_name != "the host"):
                            availability = call_data.get("host_availability", "")
                            host_email = call_data.get("host_email", "")
                            if "host_name" in call_data and call_data["host_name"]:
                                host_name = call_data["host_name"]
                            print(f"\n=== WEBSOCKET: FOUND PARAMETERS IN ACTIVE CALLS ===")
                            print(f"Call SID: '{call_sid}'")
                            print(f"Stream SID: '{stream_sid}'")
                            print(f"Availability: '{availability}'")
                            print(f"Host Email: '{host_email}'")
                            print(f"Host Name: '{host_name}'")
                            print(f"=================================================\n")
                            break
                    
                    # Also try to get parameters from call_params
                    if not (availability or host_email or host_name != "the host"):
                        print(f"\n=== WEBSOCKET: CHECKING CALL PARAMS ===")
                        print(f"Call params: {call_manager.call_params}")
                        print(f"Checking for stream SID: '{stream_sid}'")
                        print(f"====================================\n")
                        
                        call_params = call_manager.get_call_params(stream_sid)
                        if call_params:
                            availability = call_params.get("availability", "")
                            host_email = call_params.get("host_email", "")
                            if "host_name" in call_params and call_params["host_name"]:
                                host_name = call_params["host_name"]
                            print(f"\n=== WEBSOCKET: USING PARAMETERS FROM CALL PARAMS ===")
                            print(f"Stream SID: '{stream_sid}'")
                            print(f"Availability: '{availability}'")
                            print(f"Host Email: '{host_email}'")
                            print(f"Host Name: '{host_name}'")
                            print(f"===================================================\n")
                    
                    # Extract host name from email only if we don't already have a name
                    if not host_name or host_name == "the host":
                        if host_email and "@" in host_email:
                            host_name = host_email.split("@")[0]
                            # Capitalize and replace dots/underscores with spaces
                            host_name = host_name.replace(".", " ").replace("_", " ").title()
                    
                    print(f"\n=== WEBSOCKET: FINAL HOST NAME ===")
                    print(f"Host Name: '{host_name}'")
                    print(f"Host Email: '{host_email}'")
                    print("====================================\n")
                    
                    # Create the audio interface
                    audio_interface = TwilioAudioInterface(websocket)
                    
                    # Set the host availability on the audio interface
                    if availability:
                        audio_interface.set_host_availability(availability)
                    
                    # Get the current time in ISO format
                    now = datetime.datetime.now()
                    now_iso = now.isoformat()
                    
                    # Get the current day name
                    day_name = now.strftime("%A")
                    
                    # Get the timezone
                    timezone_name = time.tzname[0]
                    
                    # Prepare variables for the ElevenLabs agent
                    variables = {
                        "username": host_name,
                        "available_time": availability or "not specified",
                        "current_time_iso": now_iso,
                        "current_day": day_name,
                        "timezone_info": timezone_name
                    }
                    
                    print("\n=== WEBSOCKET: DYNAMIC VARIABLES FOR AGENT ===")
                    for key, value in variables.items():
                        print(f"  {key}: '{value}'")
                    print("===========================================\n")
                    
                    # Initialize the conversation with ElevenLabs
                    print(f"\n=== WEBSOCKET: CREATING CONVERSATION WITH ELEVENLABS ===")
                    print(f"Agent ID: {elevenlabs_controller.get_agent_id()}")
                    print(f"=======================================================\n")
                    
                    conversation = elevenlabs_controller.create_conversation(
                        audio_interface=audio_interface,
                        callback_agent_response=agent_response_callback,
                        callback_user_transcript=user_transcript_callback,
                        variables=variables  # Pass the variables here
                    )
                    
                    # Start the conversation session
                    print("\n=== WEBSOCKET: STARTING CONVERSATION SESSION ===\n")
                    conversation.start_session()
                    print("\n=== WEBSOCKET: CONVERSATION SESSION STARTED ===\n")
                    
                    # Store the conversation ID if available
                    if hasattr(conversation, 'conversation_id'):
                        print(f"\n=== WEBSOCKET: CONVERSATION ID ===")
                        print(f"ID: {conversation.conversation_id}")
                        print(f"==================================\n")
                        call_manager.set_conversation_id(stream_sid, conversation.conversation_id)
                    
                    # Register the call with the call manager
                    call_manager.register_call_with_name(stream_sid, availability, host_email, host_name)
                
                # Process the Twilio message
                if conversation:  # Only process if conversation is initialized
                    await audio_interface.handle_twilio_message(data)
                
            except Exception as e:
                print(f"\n=== WEBSOCKET: ERROR PROCESSING MESSAGE ===")
                print(f"Error: {str(e)}")
                print(f"===========================================\n")
                traceback.print_exc()

    except Exception as e:
        print(f"\n=== WEBSOCKET: ERROR IN CONNECTION ===")
        print(f"Error: {str(e)}")
        print(f"===================================\n")
        import traceback
        traceback.print_exc()
    finally:
        if 'conversation' in locals() and conversation:
            print("\n=== WEBSOCKET: ENDING CONVERSATION SESSION ===\n")
            try:
                conversation.end_session()
                conversation.wait_for_session_end()
                print("\n=== WEBSOCKET: CONVERSATION SESSION ENDED ===\n")
                
                # Format the complete transcript
                if full_transcript and stream_sid:
                    print("\n=== WEBSOCKET: SAVING COMPLETE TRANSCRIPT ===")
                    formatted_transcript = "\n".join([f"{entry['role'].capitalize()}: {entry['content']}" for entry in full_transcript])
                    
                    print(f"Full transcript length: {len(formatted_transcript)} characters")
                    print(f"Transcript preview: {formatted_transcript[:200]}..." if len(formatted_transcript) > 200 else formatted_transcript)
                    
                    # Save to the call manager directly
                    call_manager.active_calls[stream_sid]["transcript"] = full_transcript
                    
                    # Get the parameters from the call manager
                    host_availability = call_manager.active_calls[stream_sid].get("host_availability", "")
                    host_email = call_manager.active_calls[stream_sid].get("host_email", "")
                    host_name = call_manager.active_calls[stream_sid].get("host_name", "")
                    
                    # Now parse the transcript directly
                    print("\n=== WEBSOCKET: DIRECTLY PARSING TRANSCRIPT ===")
                    try:
                        # Get the text parser controller
                        text_parser = get_text_parser_controller()
                        
                        # Process the transcript right here
                        meeting_details = text_parser.parse_to_json(formatted_transcript, host_availability, host_name)
                        
                        print(f"Meeting details extracted: {meeting_details}")
                        
                        # Store the meeting details in the call manager
                        if stream_sid:
                            call_manager.active_calls[stream_sid]["meeting_details"] = meeting_details
                        
                        # No need to create calendar event here, just log details
                        form_data = meeting_details.get("formData", {})
                        print(f"  =======================PHONE CALL DETAILS=======================")
                        print(f"  Title: {form_data.get('title', '')}")
                        print(f"  Description: {form_data.get('description', '')}")
                        print(f"  Start Time: {form_data.get('startDateTime', '')}")
                        print(f"  End Time: {form_data.get('endDateTime', '')}")
                        print(f"  ================================================================")

                        # Send meeting details through WebSocket
                        try:
                            await websocket.send_json({
                                "type": "meeting_details",
                                "data": meeting_details
                            })
                            print("\n=== WEBSOCKET: SENT MEETING DETAILS ===")
                        except Exception as e:
                            print(f"\n=== WEBSOCKET: ERROR SENDING MEETING DETAILS ===")
                            print(f"Error: {str(e)}")
                            print(f"===========================================\n")
                    except Exception as e:
                        print(f"\n=== WEBSOCKET: ERROR PROCESSING TRANSCRIPT ===")
                        print(f"Error: {str(e)}")
                        print(f"=================================================\n")
                else:
                    print("\n=== WEBSOCKET: NO TRANSCRIPT TO PROCESS ===")
                    print(f"Transcript list length: {len(full_transcript)}")
                    print(f"Stream SID: {stream_sid}")
                
                # Create calendar event if we have valid meeting details
                if form_data and host_email:
                    try:
                        print("\n=== CREATING CALENDAR EVENT ===")
                        # Get tokens from Firebase
                        tokens = await firebase_service.get_user_tokens(host_email)
                        if not tokens:
                            print(f"No tokens found for user: {host_email}")
                            raise HTTPException(status_code=404, detail="User tokens not found")
                        
                        # Format the meeting data for Google Calendar
                        calendar_event_data = calendar_service.format_meeting_for_calendar(form_data)
                        
                        # Create the event using the access token
                        event_result = await calendar_service.create_event(
                            access_token=tokens["access_token"],
                            calendar_id="primary",
                            event_data=calendar_event_data
                        )
                        
                        print(f"Calendar event created successfully: {event_result}")
                        
                        # Store the event ID with the call data
                        call_manager.active_calls[stream_sid]["calendar_event_id"] = event_result.get("id")
                        
                    except Exception as e:
                        print(f"Error creating calendar event: {str(e)}")
                        # Don't raise the exception - we still want to clean up the call data
                
            except Exception as e:
                print(f"\n=== WEBSOCKET: ERROR ENDING CONVERSATION SESSION ===")
                print(f"Error: {str(e)}")
                print(f"===================================================\n")
                traceback.print_exc()

@router.post("/status")
async def twilio_status_callback(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")
    
    print(f"\n=== STATUS CALLBACK: CALL STATUS UPDATE ===")
    print(f"Call SID: '{call_sid}'")
    print(f"Call Status: '{call_status}'")
    print(f"All Form Data: {dict(form_data)}")
    print(f"=========================================\n")
    
    # If this is the first status update, store the association
    if call_status == "in-progress":
        # Get the pending parameters
        pending_params = call_manager.get_pending_params(call_sid)
        if pending_params:
            print(f"\n=== STATUS CALLBACK: FOUND PENDING PARAMS ===")
            print(f"Pending Params: {pending_params}")
            print(f"===========================================\n")
            
            # Store them with the call
            call_manager.register_call_with_name(
                call_sid,  # Use call_sid as stream_sid temporarily
                pending_params.get("availability", ""),
                pending_params.get("host_email", ""),
                pending_params.get("host_name", "")  # Include host name
            )
    
    # Process completed calls
    if call_status == "completed":
        print(f"\n=== STATUS CALLBACK: CALL COMPLETED ===")
        
        # Get the call data
        call_data = call_manager.get_call_data(call_sid)
        
        if call_data:
            print(f"Call data found for SID: {call_sid}")
            
            # Get the locally stored transcript directly
            transcript = call_manager.get_formatted_transcript(call_sid)
            
            print(f"Transcript length: {len(transcript) if transcript else 0} characters")
            print(f"Transcript preview: {transcript[:200]}..." if transcript and len(transcript) > 200 else transcript)
            
            # Get availability and host info
            host_availability = call_data.get("host_availability")
            host_email = call_data.get("host_email")
            host_name = call_data.get("host_name", "Unknown Host")
            
            print(f"Host Name: {host_name}")
            print(f"Host Email: {host_email}")
            print(f"Host Availability: {host_availability}")
            
            try:
                # Get the text parser controller
                text_parser = get_text_parser_controller()
                
                # Process the transcript
                print(f"\n=== STATUS CALLBACK: PROCESSING TRANSCRIPT ===")
                
                if transcript:
                    # Parse the transcript
                    print(f"Calling parse_to_json with transcript and host_availability")
                    meeting_details = text_parser.parse_to_json(transcript, host_availability, host_name)
                    
                    print(f"Meeting details extracted: {meeting_details}")

                    form_data = meeting_details.get("formData", {})
                    print(f"\n=== EXTRACTED MEETING DETAILS ===")
                    print(f"  Title: {form_data.get('title', '')}")
                    print(f"  Description: {form_data.get('description', '')}")
                    print(f"  Start Time: {form_data.get('startDateTime', '')}")
                    print(f"  End Time: {form_data.get('endDateTime', '')}")
                    print(f"===================================\n")
                    
                    # Create calendar event if we have valid meeting details
                    if form_data and host_email:
                        try:
                            print("\n=== CREATING CALENDAR EVENT ===")
                            # Get tokens from Firebase
                            tokens = await firebase_service.get_user_tokens(host_email)
                            if not tokens:
                                print(f"No tokens found for user: {host_email}")
                                raise HTTPException(status_code=404, detail="User tokens not found")
                            
                            # Format the meeting data for Google Calendar
                            calendar_event_data = calendar_service.format_meeting_for_calendar(form_data)
                            
                            # Create the event using the access token
                            event_result = await calendar_service.create_event(
                                access_token=tokens["access_token"],
                                calendar_id="primary",
                                event_data=calendar_event_data
                            )
                            
                            print(f"Calendar event created successfully: {event_result}")
                            
                            # Store the event ID with the call data
                            call_manager.active_calls[call_sid]["calendar_event_id"] = event_result.get("id")
                            
                        except Exception as e:
                            print(f"Error creating calendar event: {str(e)}")
                            # Don't raise the exception - we still want to clean up the call data
                    
                else:
                    print("WARNING: No transcript available for processing")
            except Exception as e:
                print(f"\n=== STATUS CALLBACK: ERROR PROCESSING TRANSCRIPT ===")
                print(f"Error: {str(e)}")
                print(f"=================================================\n")
                traceback.print_exc()
            
            finally:
                # Clean up
                print("\n=== STATUS CALLBACK: REMOVING CALL DATA ===\n")
                call_manager.remove_call(call_sid)
    
    return {"status": "received"}

@router.post("/voice-test")
async def twilio_voice_test(request: Request):
    """
    Simple test endpoint for Twilio calls
    """
    twiml = """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say>This is a test call from our scheduling assistant. The system is working correctly.</Say>
    </Response>"""
    
    return Response(content=twiml, media_type="application/xml")

@router.post("/voice-simple")
async def twilio_voice_simple(request: Request):
    """
    Simple TwiML response for testing
    """
    twiml = VoiceResponse()
    twiml.say("This is a test call from our scheduling assistant. The system is working correctly.")
    
    return Response(content=str(twiml), media_type="application/xml")

@router.post("/test-params")
async def test_params(request: CallRequest):
    """Test endpoint to verify parameters are being received correctly"""
    print("\n=== TEST PARAMS: RECEIVED REQUEST ===")
    print(f"Phone Number: '{request.phone_number}'")
    print(f"Host Availability: '{request.host_availability}'")
    print(f"Host Email: '{request.host_email}'")
    print(f"Host Name: '{request.host_name}'")  # Log the name
    print("====================================\n")
    
    return {
        "status": "success",
        "received_params": {
            "phone_number": request.phone_number,
            "host_availability": request.host_availability,
            "host_email": request.host_email,
            "host_name": request.host_name  # Include the name in the response
        }
    }

@router.get("/meeting-details/{call_sid}")
async def get_meeting_details(call_sid: str):
    """Get meeting details for a specific call"""
    try:
        # Get the call data from call_manager
        call_data = call_manager.get_call_data(call_sid)
        
        if not call_data:
            return {"success": False, "error": "Call not found"}
        
        # Get transcript and extract meeting details if needed
        transcript = call_manager.get_formatted_transcript(call_sid)
        
        # Check if meeting details already exist
        if "meeting_details" in call_data:
            form_data = call_data["meeting_details"].get("formData", {})
            return {"success": True, "formData": form_data}
        
        # If no meeting details but we have a transcript, try to extract them
        if transcript:
            text_parser = get_text_parser_controller()
            host_availability = call_data.get("host_availability", "")
            host_name = call_data.get("host_name", "")
            
            # Parse transcript to get meeting details
            meeting_details = text_parser.parse_to_json(transcript, host_availability, host_name)
            
            # Store the meeting details in the call_manager
            call_manager.active_calls[call_sid]["meeting_details"] = meeting_details
            
            return {"success": True, "formData": meeting_details.get("formData", {})}
        
        return {"success": False, "error": "No meeting details available"}
    
    except Exception as e:
        logger.error(f"Error getting meeting details: {str(e)}")
        return {"success": False, "error": str(e)} 