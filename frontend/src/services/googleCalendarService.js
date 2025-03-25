// Google Calendar API service

// Base URL for Google Calendar API
const CALENDAR_API_BASE_URL = 'https://www.googleapis.com/calendar/v3';

// Get a list of the user's calendars
export const listCalendars = async (accessToken) => {
  try {
    const response = await fetch(`${CALENDAR_API_BASE_URL}/users/me/calendarList`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch calendars: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error listing calendars:', error);
    throw error;
  }
};

// Create a new event in the user's calendar
export const createEvent = async (accessToken, calendarId = 'primary', eventData) => {
  try {
    console.log("Creating calendar event with token:", accessToken.substring(0, 10) + "...");
    console.log("Calendar ID:", calendarId);
    console.log("Event data:", JSON.stringify(eventData, null, 2));
    
    const response = await fetch(`${CALENDAR_API_BASE_URL}/calendars/${calendarId}/events`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(eventData)
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error("Calendar API error response:", errorText);
      throw new Error(`Failed to create event: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error creating event:', error);
    throw error;
  }
};

// Add this function to ensure dates are in ISO format
const ensureISOFormat = (dateString) => {
  // If it's already in ISO format, return it
  if (/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(dateString)) {
    return dateString;
  }
  
  // Otherwise, try to convert it
  try {
    const date = new Date(dateString);
    return date.toISOString();
  } catch (e) {
    console.error("Invalid date format:", dateString);
    throw new Error("Invalid date format");
  }
};

// Format meeting data for Google Calendar API
export const formatMeetingForCalendar = (meetingData) => {
  return {
    summary: meetingData.title,
    description: meetingData.description,
    start: {
      dateTime: ensureISOFormat(meetingData.startDateTime),
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    },
    end: {
      dateTime: ensureISOFormat(meetingData.endDateTime),
      timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone
    }
  };
};

// Test if the token has calendar permissions
export const testCalendarAccess = async (accessToken) => {
  try {
    console.log("Testing calendar access with token");
    
    // Try to list calendars as a simple test
    const response = await fetch(`${CALENDAR_API_BASE_URL}/users/me/calendarList`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error("Calendar API test failed:", errorText);
      return { success: false, error: `Status: ${response.status}, Details: ${errorText}` };
    }
    
    const data = await response.json();
    return { 
      success: true, 
      calendars: data.items?.length || 0,
      primaryCalendarId: data.items?.find(cal => cal.primary)?.id || 'primary'
    };
  } catch (error) {
    console.error('Error testing calendar access:', error);
    return { success: false, error: error.message };
  }
}; 