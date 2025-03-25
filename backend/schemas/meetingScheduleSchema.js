const meetingScheduleSchema = {
    "title": "Meeting Schedule Schema",
    "description": "A schema representing the structure of the meeting scheduling form.",
    "type": "object",
    "properties": {
        "title": {
            "type": "string",
            "description": "The title or subject of the meeting"
        },
        "description": {
            "type": "string",
            "description": "A description of what the meeting is about"
        },
        "startDateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The start date and time of the meeting in ISO 8601 format"
        },
        "endDateTime": {
            "type": "string",
            "format": "date-time",
            "description": "The end date and time of the meeting in ISO 8601 format"
        },
        "location": {
            "type": "string",
            "description": "The location of the meeting (physical or virtual)"
        },
        "attendees": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the attendee"
                    },
                    "email": {
                        "type": "string",
                        "description": "The email address of the attendee"
                    }
                },
                "required": ["name"]
            },
            "description": "List of people attending the meeting"
        },
        "organizer": {
            "type": "string",
            "description": "The person organizing the meeting"
        },
        "timezone": {
            "type": "string",
            "description": "The timezone for the meeting times"
        }
    },
    "required": ["title", "startDateTime", "endDateTime"]
};

export { meetingScheduleSchema }; 