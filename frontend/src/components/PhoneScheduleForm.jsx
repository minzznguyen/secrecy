import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { initiateCall } from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { FiPhone } from 'react-icons/fi';

export function PhoneScheduleForm({ userAvailability, onCallComplete }) {
  const { currentUser } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [callStatus, setCallStatus] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  // Get user's name from their profile
  const userName = currentUser?.displayName || 'User';
  
  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);
  
  const setupWebSocket = () => {
    try {
      // Close existing connection if any
      if (wsRef.current) {
        wsRef.current.close();
      }
      
      // Set up WebSocket connection
      const websocket = new WebSocket('ws://localhost:8000/ws/twilio');
      wsRef.current = websocket;
      
      websocket.onopen = () => {
        console.log('WebSocket connection established');
      };
      
      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          
          if (data.type === 'meeting_details') {
            console.log('Meeting details received:', data.data);
            if (onCallComplete) {
              onCallComplete(data.data);
            }
          }
        } catch (error) {
          console.error('Error processing WebSocket message:', error);
        }
      };
      
      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Don't close the connection on error, let it try to reconnect
      };
      
      websocket.onclose = () => {
        console.log('WebSocket connection closed');
        // Attempt to reconnect after a delay
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect WebSocket...');
          setupWebSocket();
        }, 3000); // Wait 3 seconds before reconnecting
      };
    } catch (error) {
      console.error('Error setting up WebSocket:', error);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setCallStatus(null);
    
    console.log("=== PHONE FORM: SUBMITTING CALL REQUEST ===");
    console.log("Phone Number:", phoneNumber);
    console.log("User Name:", userName);
    console.log("User Availability:", userAvailability);
    console.log("User Email:", currentUser?.email);
    console.log("=========================================");
    
    try {
      const response = await initiateCall(
        phoneNumber, 
        userAvailability,
        currentUser?.email,
        userName
      );
      
      console.log("Call initiated:", response);
      if (response.status === "success") {
        setCallStatus({ 
          success: true, 
          message: 'Call initiated successfully! You will receive a call shortly.' 
        });

        // Wait a short delay before connecting to WebSocket
        setTimeout(() => {
          setupWebSocket();
        }, 1000); // Wait 1 second before connecting
      } else {
        setCallStatus({ 
          success: false, 
          message: `Failed to initiate call: ${response.message}`
        });
      }
    } catch (error) {
      console.error("Error initiating call:", error);
      setCallStatus({ 
        success: false, 
        message: 'An error occurred while initiating the call. Please try again.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return (
    <div className="mt-6 p-4 border rounded-md bg-white shadow-sm">
      <h3 className="text-lg font-medium mb-4">Schedule a Phone Call</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="phoneNumber" className="block text-sm font-medium text-gray-700 mb-1">
            Phone Number
          </label>
          <Input
            id="phoneNumber"
            type="tel"
            placeholder="Enter phone number"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            required
          />
        </div>
        
        <div>
          <Button 
            type="submit" 
            disabled={isSubmitting || !userAvailability}
            className="flex items-center gap-2 w-full"
          >
            <FiPhone size={16} />
            {isSubmitting ? 'Initiating Call...' : 'Schedule Call'}
          </Button>
        </div>
        
        {!userAvailability && (
          <p className="text-amber-600 text-sm">
            Please set your availability before scheduling a call.
          </p>
        )}
        
        {callStatus && (
          <div className={`mt-4 p-3 rounded-md ${callStatus.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
            {callStatus.message}
          </div>
        )}
      </form>
    </div>
  );
} 