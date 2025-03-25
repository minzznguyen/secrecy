import os
import logging
from fastapi import HTTPException
from twilio.rest import Client
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TwilioController:
    def __init__(self):
        # Get Twilio credentials from environment variables
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")
        self.elevenlabs_agent_id = os.getenv("ELEVENLABS_AGENT_ID")
        self.ngrok_url = os.getenv("NGROK_URL")
        
        # Check if Twilio credentials are set
        if not all([self.account_sid, self.auth_token, self.twilio_phone]):
            logger.warning("Twilio credentials not fully configured")
        else:
            # Initialize Twilio client
            self.client = Client(self.account_sid, self.auth_token)
            logger.info("Twilio controller initialized")
    
    async def initiate_call(self, phone_number, host_availability=None, host_email=None, host_name=None):
        """
        Initiate a call to the customer
        
        Args:
            phone_number (str): Customer's phone number
            host_availability (str, optional): Host's availability
            host_email (str, optional): Host's email address
            host_name (str, optional): Host's name
            
        Returns:
            dict: Call details
        """
        print("\n=== TWILIO CONTROLLER: INITIATING CALL ===")
        print(f"Phone Number: '{phone_number}'")
        print(f"Host Availability: '{host_availability}'")
        print(f"Host Email: '{host_email}'")
        print(f"Host Name: '{host_name}'")
        print("=========================================\n")
        
        # Format the phone number
        to_number = phone_number.strip()
        
        # If the number doesn't start with +, add the country code
        if not to_number.startswith('+'):
            # If it's a 10-digit US number, add +1
            if len(to_number) == 10 and to_number.isdigit():
                to_number = f"+1{to_number}"
            # Otherwise just add + (assuming it already has country code)
            else:
                to_number = f"+{to_number}"
        
        print(f"\n=== TWILIO CONTROLLER: FORMATTED PHONE NUMBER ===")
        print(f"Original: '{phone_number}'")
        print(f"Formatted: '{to_number}'")
        print(f"==============================================\n")
        
        # Construct the webhook URL with properly encoded parameters
        webhook_url = f"{self.ngrok_url}/api/twilio/voice"
        
        # Add query parameters with proper URL encoding
        params = {}
        if host_availability:
            params['availability'] = host_availability
        if host_email:
            params['host_email'] = host_email
        if host_name:
            params['host_name'] = host_name
            
        # Add parameters to URL if we have any
        if params:
            query_string = "&".join([f"{k}={urllib.parse.quote(v)}" for k, v in params.items()])
            webhook_url = f"{webhook_url}?{query_string}"
        
        print("\n=== TWILIO CONTROLLER: WEBHOOK URL ===")
        print(f"Webhook URL: '{webhook_url}'")
        print("======================================\n")
        
        try:
            # Initiate the call
            call = self.client.calls.create(
                to=to_number,
                from_=self.twilio_phone,
                url=webhook_url,
                status_callback=f"{self.ngrok_url}/api/twilio/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed'],
                status_callback_method='POST'
            )
            
            print(f"\n=== TWILIO CONTROLLER: CALL INITIATED ===")
            print(f"Call SID: {call.sid}")
            print(f"Call Status: {call.status}")
            print(f"To Number: {to_number}")
            print("=========================================\n")
            
            return {
                "status": "success",
                "message": "Call initiated",
                "call_sid": call.sid
            }
        
        except Exception as e:
            logger.error(f"Error initiating call: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            } 