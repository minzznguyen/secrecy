import os
import logging
from elevenlabs import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ConversationInitiationData
from dotenv import load_dotenv
import requests
import aiohttp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElevenLabsController:
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("AGENT_ID")
        self.client = ElevenLabs(api_key=self.api_key)
        self.base_url = "https://api.elevenlabs.io/v1"
        
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not set in environment variables")
        
        logger.info("ElevenLabsController initialized")
        
    def get_client(self):
        """Get the ElevenLabs client instance"""
        return self.client
    
    def get_agent_id(self):
        """Get the ElevenLabs agent ID"""
        return self.agent_id
    
    def create_conversation(self, audio_interface, callback_agent_response=None, callback_user_transcript=None, variables=None):
        """
        Create a conversation with the ElevenLabs agent
        
        Args:
            audio_interface: The audio interface to use
            callback_agent_response: Callback for agent responses
            callback_user_transcript: Callback for user transcripts
            variables: Dictionary of variables to pass to the agent
        """
        try:
            print("\n=== ELEVENLABS CONTROLLER: CREATING CONVERSATION ===")
            print(f"Agent ID: {self.agent_id}")
            print(f"API Key: {self.api_key[:5]}...{self.api_key[-5:]}")
            print("===================================================\n")
            
            # Define default callbacks if none provided
            def agent_response_wrapper(text):
                print(f"\n=== ELEVENLABS CONTROLLER: AGENT RESPONSE ===")
                print(f"Text: {text}")
                print(f"===========================================\n")
                if callback_agent_response:
                    callback_agent_response(text)
                
            def user_transcript_wrapper(text):
                print(f"\n=== ELEVENLABS CONTROLLER: USER TRANSCRIPT ===")
                print(f"Text: {text}")
                print(f"============================================\n")
                if callback_user_transcript:
                    callback_user_transcript(text)
            
            # Set default variables if none provided
            if variables is None:
                variables = {
                    "username": "the user",
                    "available_time": "Monday to Friday, 9 AM to 5 PM",
                    "current_time_iso": "2023-03-23T14:30:00Z",
                    "current_day": "Thursday",
                    "timezone_info": "Eastern Time (ET)"
                }
                print("\n=== ELEVENLABS CONTROLLER: USING DEFAULT VARIABLES ===\n")
            else:
                print("\n=== ELEVENLABS CONTROLLER: USING PROVIDED VARIABLES ===\n")
            
            # Print variables in a more readable format
            print("\n=== ELEVENLABS CONTROLLER: DYNAMIC VARIABLES ===")
            for key, value in variables.items():
                print(f"  {key}: '{value}'")
            print("==============================================\n")
            
            # Create a ConversationInitiationData object with dynamic variables
            config = ConversationInitiationData(dynamic_variables=variables)
            print("\n=== ELEVENLABS CONTROLLER: CREATED CONFIG OBJECT ===")
            print(f"Config: {config}")
            print("=================================================\n")
            
            # Create the conversation
            print("\n=== ELEVENLABS CONTROLLER: INITIALIZING CONVERSATION ===\n")
            conversation = Conversation(
                client=self.client,
                agent_id=self.agent_id,
                config=config,  # Use the config object
                requires_auth=False,
                audio_interface=audio_interface,
                callback_agent_response=agent_response_wrapper,
                callback_user_transcript=user_transcript_wrapper
            )
            
            print("\n=== ELEVENLABS CONTROLLER: CONVERSATION CREATED ===\n")
            
            # Try to access and log any relevant properties of the conversation object
            print("\n=== ELEVENLABS CONTROLLER: CONVERSATION PROPERTIES ===")
            try:
                if hasattr(conversation, 'conversation_id'):
                    print(f"Conversation ID: {conversation.conversation_id}")
                if hasattr(conversation, 'agent_id'):
                    print(f"Agent ID: {conversation.agent_id}")
                if hasattr(conversation, 'config'):
                    print(f"Config: {conversation.config}")
                if hasattr(conversation, 'dynamic_variables'):
                    print(f"Dynamic Variables: {conversation.dynamic_variables}")
            except Exception as e:
                print(f"Error accessing conversation properties: {str(e)}")
            print("===================================================\n")
            
            return conversation
        except Exception as e:
            print(f"\n=== ELEVENLABS CONTROLLER: ERROR CREATING CONVERSATION ===")
            print(f"Error: {str(e)}")
            print(f"========================================================\n")
            import traceback
            traceback.print_exc()
            raise

    async def start_conversation(self, text_input=None):
        """Start a conversation with the Eleven Labs agent using text input"""
        try:
            logger.info(f"Starting conversation with agent {self.agent_id}")
            
            # Store conversation transcript
            conversation_transcript = []
            
            # Define callbacks to capture the conversation
            def agent_response_callback(response):
                logger.info(f"Agent: {response}")
                conversation_transcript.append({"role": "agent", "content": response})
                
            def user_transcript_callback(transcript):
                logger.info(f"User: {transcript}")
                conversation_transcript.append({"role": "user", "content": transcript})
            
            # Initialize conversation
            conversation = Conversation(
                client=self.client,
                agent_id=self.agent_id,
                requires_auth=False,
                callback_agent_response=agent_response_callback,
                callback_user_transcript=user_transcript_callback,
            )
            
            # If text input is provided, use it instead of audio
            if text_input:
                # Start session
                conversation.start_session()
                
                # Send text input
                conversation.send_text(text_input)
                
                # Wait for response and end session
                response = await conversation.get_response()
                conversation_transcript.append({"role": "agent", "content": response})
                
                conversation.end_session()
                
                # Get conversation ID
                conversation_id = conversation.conversation_id
                
                # Convert transcript to a single string for text parser
                full_transcript = "\n".join([f"{item['role'].capitalize()}: {item['content']}" for item in conversation_transcript])
                
                return {
                    "status": "success",
                    "conversation_id": conversation_id,
                    "transcript": full_transcript,
                    "messages": conversation_transcript
                }
            else:
                # For audio-based conversations, we'd need WebSocket support
                # This is a placeholder for future implementation
                raise Exception("Audio-based conversations not yet implemented in this API")
                
        except Exception as e:
            logger.error(f"Error in conversation: {str(e)}")
            raise Exception(f"Error in conversation: {str(e)}")

    async def get_signed_url(self):
        """Get a signed URL for connecting to the agent"""
        try:
            logger.info(f"Getting signed URL for agent {self.agent_id}")
            
            url = f"https://api.elevenlabs.io/v1/convai/conversation/get_signed_url?agent_id={self.agent_id}"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            return {"signedUrl": data.get("signed_url")}
        
        except Exception as e:
            logger.error(f"Error getting signed URL: {str(e)}")
            raise Exception(f"Error getting signed URL: {str(e)}")
            
    async def get_conversation_details(self, conversation_id):
        """Get conversation details from ElevenLabs API"""
        logger.info(f"Getting conversation details for ID: {conversation_id}")
        
        if not self.api_key:
            raise Exception("ElevenLabs API key not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/convai/conversation/{conversation_id}"
                headers = {"xi-api-key": self.api_key}
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs API error: {error_text}")
                        raise Exception(
                            f"ElevenLabs API error: {error_text}"
                        )
                    
                    data = await response.json()
                    logger.info(f"Successfully retrieved conversation details")
                    return data
                    
        except aiohttp.ClientError as e:
            logger.error(f"Error connecting to ElevenLabs API: {str(e)}")
            raise Exception(
                f"Error connecting to ElevenLabs API: {str(e)}"
            )
    
    async def get_conversation_transcript(self, conversation_id):
        """Get the full transcript of a conversation"""
        conversation_details = await self.get_conversation_details(conversation_id)
        
        # Extract the transcript from the conversation details
        transcript = []
        
        if "messages" in conversation_details:
            for message in conversation_details["messages"]:
                transcript.append({
                    "role": message.get("source", "unknown"),
                    "text": message.get("message", "")
                })
        
        return transcript 