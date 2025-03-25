from app.controllers.calendar_controller import CalendarController
from app.services.calendar_service import CalendarService
from app.controllers.text_parser_controller import TextParserController

# Calendar dependencies
def get_calendar_service():
    return CalendarService()

def get_calendar_controller():
    calendar_service = get_calendar_service()
    return CalendarController(calendar_service)

# Text parser dependencies
def get_text_parser_controller():
    return TextParserController() 