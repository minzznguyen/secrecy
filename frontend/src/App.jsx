import { useState, useEffect } from 'react'
import { Button } from './components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { FiLogOut, FiCheck, FiCalendar, FiActivity } from 'react-icons/fi'
import { format } from 'date-fns'
import { useAuth } from './contexts/AuthContext'
import { signOut } from 'firebase/auth'
import { auth } from './lib/firebase'
import { LoginPage } from './pages/LoginPage'
import { OAuthCallback } from './pages/OAuthCallback'
import { WeeklyAvailability } from './components/WeeklyAvailability'
import { PhoneScheduleForm } from './components/PhoneScheduleForm'
import { createEventWithRefresh, formatMeetingForCalendar, testCalendarAccess } from './services/googleCalendarService'
import { testCalendarService } from './services/api'
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom'

function AppContent() {
  useEffect(() => {
    document.title = "Secrely";
  }, []);
  
  const { currentUser, googleAccessToken } = useAuth();
  const [error, setError] = useState(null)
  const [meetingData, setMeetingData] = useState({
    title: '',
    startDateTime: '',
    endDateTime: '',
    description: ''
  })
  const [userAvailability, setUserAvailability] = useState('');
  const [calendarStatus, setCalendarStatus] = useState(null);
  const [testStatus, setTestStatus] = useState(null);
  const location = useLocation();
  
  // Format ISO date string to a more readable format
  const formatDateTime = (isoString) => {
    if (!isoString) return ''
    try {
      const date = new Date(isoString)
      return format(date, 'PPpp') // e.g., "Apr 29, 2023, 1:30 PM"
    } catch (e) {
      return isoString
    }
  }
  
  // If user is not authenticated, show login page
  if (!currentUser) {
    console.log("No user, showing login page");
    return <LoginPage />;
  }
  
  console.log("User authenticated, showing main app");
  
  // Handle sign out
  const handleSignOut = async () => {
    try {
      await signOut(auth);
    } catch (error) {
      console.error('Error signing out:', error);
    }
  };
  
  // Handle availability save
  const handleAvailabilitySave = (formattedAvailability) => {
    setUserAvailability(formattedAvailability);
    console.log('Availability saved:', formattedAvailability);
  };

  // Handle call completion
  const handleCallComplete = (meetingDetails) => {
    if (meetingDetails.success && meetingDetails.formData) {
      console.log('Setting meeting data from call:', meetingDetails.formData)
      setMeetingData({
        title: meetingDetails.formData.title || '',
        startDateTime: meetingDetails.formData.startDateTime || '',
        endDateTime: meetingDetails.formData.endDateTime || '',
        description: meetingDetails.formData.description || ''
      })
    }
  };
  
  // Handle calendar test
  const handleCalendarTest = async () => {
    try {
      setError(null);
      setCalendarStatus('Testing calendar access...');
      
      // First test if we have calendar access
      const accessTest = await testCalendarAccess(googleAccessToken);
      
      if (!accessTest.success) {
        setCalendarStatus('Calendar access test failed: ' + accessTest.error);
        return;
      }
      
      // If we have access, try to create a test event
      const testEvent = {
        title: 'Test Meeting',
        startDateTime: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
        endDateTime: new Date(Date.now() + 7200000).toISOString(),   // 2 hours from now
        description: 'This is a test meeting created by the Meeting Scheduler AI'
      };
      
      const formattedEvent = formatMeetingForCalendar(testEvent);
      const result = await createEventWithRefresh(accessTest.primaryCalendarId, formattedEvent);
      
      setCalendarStatus('Success! Test event created. Event ID: ' + result.id);
    } catch (error) {
      console.error('Calendar test error:', error);
      setCalendarStatus('Error: ' + error.message);
      setError(error.message);
    }
  };

  // Handle backend calendar service test
  const handleBackendCalendarTest = async () => {
    try {
      setError(null);
      setTestStatus('Testing backend calendar service...');
      
      // Create test meeting data
      const testMeetingData = {
        title: 'Backend Test Meeting',
        startDateTime: new Date(Date.now() + 3600000).toISOString(), // 1 hour from now
        endDateTime: new Date(Date.now() + 7200000).toISOString(),   // 2 hours from now
        description: 'This is a test meeting created by the backend calendar service'
      };
      
      // Test the backend service
      const result = await testCalendarService(currentUser.uid, testMeetingData);
      
      if (result.success) {
        setTestStatus(`Success! Event created. ID: ${result.event_id}`);
      } else {
        setTestStatus('Error: ' + result.detail);
      }
    } catch (error) {
      console.error('Backend calendar test error:', error);
      setTestStatus('Error: ' + error.message);
      setError(error.message);
    }
  };
  
  // Main app UI for authenticated users
  return (
    <div className="container mx-auto py-8 max-w-2xl">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-center">Meeting Scheduler AI</CardTitle>
            <CardDescription className="text-center">
              Schedule a meeting via phone call
            </CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleSignOut}
            className="flex items-center gap-1"
          >
            <FiLogOut size={16} />
            Sign Out
          </Button>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* User info */}
          <div className="text-sm text-gray-500 text-center">
            Signed in as: {currentUser.email}
          </div>
          
          {/* Weekly Availability Form */}
          <WeeklyAvailability onSave={handleAvailabilitySave} />
          
          {/* Show availability summary if available */}
          {userAvailability && (
            <div className="text-sm bg-gray-50 p-3 rounded-md border mb-6">
              <div className="font-medium mb-1 flex items-center">
                <span>Current Availability</span>
                <FiCheck className="ml-2 text-green-500" size={16} />
              </div>
              <div className="text-gray-600">{userAvailability}</div>
            </div>
          )}
          
          {/* Phone Schedule Form */}
          {userAvailability && (
            <PhoneScheduleForm 
              userAvailability={userAvailability} 
              onCallComplete={handleCallComplete}
            />
          )}
          
          {/* Meeting Data Form */}
          <div className="mt-6 p-4 border rounded-lg bg-gray-50">
            <h3 className="text-lg font-medium mb-4 flex items-center">
              Meeting Details
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={meetingData.title}
                  readOnly
                  className="w-full p-2 border rounded-md bg-white"
                  placeholder="Meeting title will appear here"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                  <input
                    type="text"
                    value={formatDateTime(meetingData.startDateTime)}
                    readOnly
                    className="w-full p-2 border rounded-md bg-white"
                    placeholder="Start time"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">End Time</label>
                  <input
                    type="text"
                    value={formatDateTime(meetingData.endDateTime)}
                    readOnly
                    className="w-full p-2 border rounded-md bg-white"
                    placeholder="End time"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={meetingData.description}
                  readOnly
                  rows={3}
                  className="w-full p-2 border rounded-md bg-white"
                  placeholder="Meeting description will appear here"
                />
              </div>
              
              {/* Add Calendar Test Buttons */}
              <div className="mt-4 space-y-4">
                <Button
                  type="button"
                  variant="outline"
                  className="w-full flex items-center justify-center gap-2"
                  onClick={handleCalendarTest}
                  disabled={!googleAccessToken}
                >
                  <FiCalendar size={16} />
                  Test Frontend Calendar
                </Button>
                
                <Button
                  type="button"
                  variant="outline"
                  className="w-full flex items-center justify-center gap-2"
                  onClick={handleBackendCalendarTest}
                  disabled={!currentUser}
                >
                  <FiActivity size={16} />
                  Test Backend Calendar
                </Button>
                
                {calendarStatus && (
                  <div className={`mt-2 text-sm ${calendarStatus.includes('Success') ? 'text-green-600' : 'text-red-600'}`}>
                    {calendarStatus}
                  </div>
                )}
                
                {testStatus && (
                  <div className={`mt-2 text-sm ${testStatus.includes('Success') ? 'text-green-600' : 'text-red-600'}`}>
                    {testStatus}
                  </div>
                )}
              </div>
            </div>
          </div>
          
          {error && <p className="text-red-500 text-center">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/oauth/callback" element={<OAuthCallback />} />
        <Route path="*" element={<AppContent />} />
      </Routes>
    </Router>
  );
}

export default App; 