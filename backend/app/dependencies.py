from app.controllers.meeting_controller import MeetingController
from app.controllers.twilio_controller import TwilioController
from app.controllers.elevenlabs_controller import ElevenLabsController
from app.controllers.text_parser_controller import TextParserController

# Meeting dependencies
def get_meeting_controller():
    return MeetingController()

# Twilio dependencies
def get_twilio_controller():
    return TwilioController()

# ElevenLabs dependencies
def get_elevenlabs_controller():
    return ElevenLabsController()

# Text Parser dependencies
def get_text_parser_controller():
    return TextParserController() 