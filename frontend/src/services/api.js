// Base API URL from environment variable or default to relative path
const API_BASE_URL = 'http://localhost:8000';  // Empty string to use the proxy configuration
import { auth } from '../lib/firebase';

export const initiateCall = async (phoneNumber, hostAvailability, hostEmail, hostName) => {
  console.log("=== API SERVICE: SENDING DATA TO BACKEND ===");
  console.log("Phone Number:", phoneNumber);
  console.log("Host Availability:", hostAvailability);
  console.log("Host Email:", hostEmail);
  console.log("Host Name:", hostName);
  console.log("=========================================");
  
  const requestBody = {
    phone_number: phoneNumber,
    host_availability: hostAvailability,
    host_email: hostEmail,
    host_name: hostName
  };
  
  console.log("Request Body:", JSON.stringify(requestBody));
  
  const response = await fetch(`${API_BASE_URL}/api/twilio/call`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });
  
  const data = await response.json();
  
  console.log("=== API SERVICE: RECEIVED RESPONSE ===");
  console.log(data);
  console.log("====================================");
  
  return data;
};

export const testParams = async (phoneNumber, hostAvailability, hostEmail, hostName) => {
  console.log("=== TEST PARAMS: SENDING DATA TO BACKEND ===");
  console.log("Phone Number:", phoneNumber);
  console.log("Host Availability:", hostAvailability);
  console.log("Host Email:", hostEmail);
  console.log("Host Name:", hostName);
  console.log("=========================================");
  
  const requestBody = {
    phone_number: phoneNumber,
    host_availability: hostAvailability,
    host_email: hostEmail,
    host_name: hostName
  };
  
  console.log("Request Body:", JSON.stringify(requestBody));
  
  const response = await fetch(`${API_BASE_URL}/api/twilio/test-params`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody),
  });
  
  const data = await response.json();
  
  console.log("=== TEST PARAMS: RECEIVED RESPONSE ===");
  console.log(data);
  console.log("====================================");
  
  return data;
};

export const testCalendarService = async (user_id, meeting_data) => {
  try {
    console.log("=== API SERVICE: TESTING CALENDAR SERVICE ===");
    console.log("User ID:", user_id);
    console.log("Meeting Data:", meeting_data);
    console.log("=========================================");
    
    // Get the current user's ID token
    const idToken = await auth.currentUser.getIdToken();
    
    const response = await fetch(`${API_BASE_URL}/api/calendar/create-event`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${idToken}`
      },
      body: JSON.stringify({
        user_id,
        meeting_data
      }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    console.log("=== API SERVICE: CALENDAR SERVICE RESPONSE ===");
    console.log(data);
    console.log("============================================");
    
    return data;
  } catch (error) {
    console.error("Error testing calendar service:", error);
    throw error;
  }
};

// Function to store Google tokens in the backend
export const storeGoogleTokens = async (user_id, email, access_token, refresh_token) => {
  try {
    console.log("=== API SERVICE: STORING GOOGLE TOKENS ===");
    console.log("User ID:", user_id);
    console.log("Email:", email);
    console.log("Access Token:", access_token ? "Yes" : "No");
    console.log("Refresh Token:", refresh_token ? "Yes" : "No");
    console.log("=========================================");
    
    const response = await fetch(`${API_BASE_URL}/api/calendar/store-tokens`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id,
        email,
        access_token,
        refresh_token,
        expires_in: 3600 // Default 1 hour
      }),
    });
    
    const data = await response.json();
    
    console.log("=== API SERVICE: TOKEN STORAGE RESPONSE ===");
    console.log(data);
    console.log("=========================================");
    
    return data;
  } catch (error) {
    console.error("Error storing Google tokens:", error);
    throw error;
  }
}; 