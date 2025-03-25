import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { initiateCall } from '../services/api';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { FiPhone } from 'react-icons/fi';

export function PhoneScheduleForm({ userAvailability }) {
  const { currentUser } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [callStatus, setCallStatus] = useState(null);
  
  // Get user's name from their profile
  const userName = currentUser?.displayName || 'User';
  
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
      setCallStatus({ 
        success: response.status === 'success', 
        message: response.status === 'success' 
          ? 'Call initiated successfully! You will receive a call shortly.' 
          : `Failed to initiate call: ${response.message}`
      });
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