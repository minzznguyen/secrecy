import json
import os
import logging
import traceback
from datetime import datetime, timezone
import pytz
from openai import OpenAI
from fastapi import HTTPException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextParserController:
    def __init__(self):
        self.client = OpenAI()  # Automatically reads API key from env
        logger.info("TextParserController initialized")

    def parse_to_json(self, transcript, host_availability=None, host_name=None):
        """
        Parse a conversation transcript to extract meeting details
        
        Args:
            transcript (str): The conversation transcript
            host_availability (str, optional): Host's availability constraints
            host_name (str, optional): Host's name
            
        Returns:
            dict: Extracted meeting details
        """
        try:
            logger.info(f"=== TEXT PARSER: PARSING CONVERSATION ===")
            logger.info(f"Transcript length: {len(transcript) if transcript else 0}")
            
            if not transcript:
                raise ValueError('No transcript provided')
            
            logger.info(f"Transcript preview: {transcript[:200]}..." if len(transcript) > 200 else transcript)
            logger.info(f"Host availability: {host_availability}")
            logger.info(f"Host name: {host_name}")

            # Get the schema directory path
            schema_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "schemas")
            logger.info(f"Schema directory path: {schema_dir}")
            
            # Check if schema directory exists
            if not os.path.exists(schema_dir):
                logger.error(f"Schema directory not found: {schema_dir}")
                raise ValueError(f"Schema directory not found: {schema_dir}")
            
            # Load the schema and example
            schema_path = os.path.join(schema_dir, 'meetingScheduleSchema.js')
            example_path = os.path.join(schema_dir, 'meetingExample.json')
            
            # Check if files exist
            if not os.path.exists(schema_path):
                logger.error(f"Schema file not found: {schema_path}")
                raise ValueError(f"Schema file not found: {schema_path}")
            
            if not os.path.exists(example_path):
                logger.error(f"Example file not found: {example_path}")
                raise ValueError(f"Example file not found: {example_path}")
            
            logger.info(f"Loading schema from: {schema_path}")
            logger.info(f"Loading example from: {example_path}")
            
            with open(schema_path, 'r') as f:
                schema_content = f.read()
                start_idx = schema_content.find('{')
                end_idx = schema_content.rfind('}') + 1
                schema_json = schema_content[start_idx:end_idx]

            with open(example_path, 'r') as f:
                example_json = f.read()

            # Get the current time in different common timezones
            current_utc = datetime.now(timezone.utc)
            
            # Get the current day of the week
            current_day = current_utc.strftime('%A')  # Full day name (e.g., Monday)
            
            timezones = {
                "US/Eastern": "America/New_York",
                "US/Central": "America/Chicago", 
                "US/Mountain": "America/Denver",
                "US/Pacific": "America/Los_Angeles"
            }
            
            timezone_info = f"Current day: {current_day}\nCurrent times:\n"
            for zone_name, zone_id in timezones.items():
                tz = pytz.timezone(zone_id)
                current_time = current_utc.astimezone(tz)
                # Include day of week for each timezone
                day_in_timezone = current_time.strftime('%A')
                timezone_info += f"- {zone_name}: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')} ({day_in_timezone})\n"
            
            # Format current UTC time in ISO 8601 format
            current_time_iso = current_utc.isoformat()

            # Build system prompt with host availability if provided
            system_content = f"""You are an AI scheduling assistant that helps parse conversations into structured meeting schedule data.
                            
                            CURRENT TIME CONTEXT:
                            Current UTC time: {current_time_iso}
                            Current day: {current_day}
                            {timezone_info}
                            
                            When suggesting meeting times, use this current time as reference and only suggest future times.
                            
                            Extract information from the conversation and format it according to this schema:
                            {schema_json}

                            Here's an example of how the output should be structured:
                            {example_json}

                            Important rules:
                            MOST IMPORTANT: Always format datetime values in ISO 8601 format (YYYY-MM-DDTHH:MM:SS±HH:MM)
                            VERY IMPORTANT: Do not include any other text or comments in your output
                            VERY IMPORTANT ALSO: look for keywords such as next week, next month, next year, etc. and use that as a reference point for suggesting meeting times to return the right value
                            1. Follow the exact structure of the example
                            2. For any string fields where information is not found in the transcript, use ""
                            3. Make sure all required fields are included in your output
                            
                            5. If no specific time is mentioned, suggest a reasonable business hour time (9 AM to 5 PM local time)
                            6. If a time is mentioned without specifying AM/PM, assume business hours (9 AM to 5 PM)
                            7. If no specific day is mentioned, suggest the next available business day (Monday through Friday)
                            8. Include timezone information in the ISO datetime format
                            """
            
            # Add host availability information if provided
            if host_availability:
                system_content += f"\nThe host is available: {host_availability}. Please ensure the suggested meeting time aligns with the host's availability."
            if host_name:
                system_content += f"\nThe host's name is {host_name}. Make sure to include the customer's name in the title of the meeting."
                
            system_content += "\n\nParse the conversation and ensure your output matches the structure of the example exactly."

            logger.info("Sending to GPT-4o-mini...")
            try:
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": transcript
                        }
                    ],
                    temperature=0.7
                )
                logger.info("GPT-4o-mini processing completed")
            except Exception as api_err:  # Use a generic Exception
                logger.error(f"OpenAI API error: {str(api_err)}")
                return {
                    'error': 'Error communicating with OpenAI API',
                    'details': str(api_err)
                }, 500

            # Get the raw response and parse it as JSON
            gpt_response = completion.choices[0].message.content.strip()

            try:
                parsed_json = json.loads(gpt_response)
                logger.info(f"Successfully parsed JSON response")
                return {
                    'success': True,
                    'formData': parsed_json
                }
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from GPT: {str(e)}")
                logger.error(f"Raw response: {gpt_response}")
                
                # Attempt to extract JSON from the response text
                import re
                json_match = re.search(r'```json\n(.*?)\n```', gpt_response, re.DOTALL)
                if json_match:
                    try:
                        parsed_json = json.loads(json_match.group(1))
                        logger.info(f"Extracted JSON from markdown code block: {parsed_json}")
                        return {
                            'success': True,
                            'formData': parsed_json
                        }
                    except Exception as ex:
                        logger.error(f"Error parsing extracted JSON: {ex}")
                
                return {
                    'error': 'Failed to parse GPT response as JSON',
                    'raw_response': gpt_response
                }, 500

        except Exception as e:
            logger.error(f"Exception: {traceback.format_exc()}")
            return {'error': str(e)}, 500