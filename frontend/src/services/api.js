// Base API URL from environment variable or default to relative path
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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