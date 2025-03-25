import { useState, useCallback, useRef, useEffect } from 'react'
import { useConversation } from '@11labs/react'
import { Button } from './components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card'
import { FiPhone, FiPhoneOff, FiCalendar, FiLogOut, FiCheck, FiTool } from 'react-icons/fi'
import { format } from 'date-fns'
import { useAuth } from './contexts/AuthContext'
import { signOut } from 'firebase/auth'
import { auth } from './lib/firebase'
import { LoginPage } from './pages/LoginPage'
import { createEvent, formatMeetingForCalendar, testCalendarAccess } from './services/googleCalendarService'
import { WeeklyAvailability } from './components/WeeklyAvailability'
import { PhoneScheduleForm } from './components/PhoneScheduleForm'
import { initiateCall, testParams } from './services/api'

function App() {
  // Add this useEffect at the top of your component
  useEffect(() => {
    // Set the document title to "Secrecy"
    document.title = "Secrely";
  }, []);
  
  const { currentUser } = useAuth();
  // Get token directly from localStorage as a fallback
  const [googleAccessToken, setLocalToken] = useState(localStorage.getItem('googleAccessToken'));
  
  // All your existing state and hooks
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [authMode, setAuthMode] = useState('signin'); // 'signin' or 'signup'
  const [messages, setMessages] = useState([])
  const messagesRef = useRef([])
  const [showTranscript, setShowTranscript] = useState(false)
  const [meetingData, setMeetingData] = useState({
    title: '',
    startDateTime: '',
    endDateTime: '',
    description: ''
  })
  const [userAvailability, setUserAvailability] = useState('');
  
  // Agent ID from your .env file
  const AGENT_ID = 'ly9ETO1086vjAbCu0OuJ'
  
  // Add a new state to track calendar success
  const [calendarSuccess, setCalendarSuccess] = useState(false);
  
  // Update the ref whenever messages change
  useEffect(() => {
    messagesRef.current = messages
  }, [messages])
  
  // Add this useEffect to keep the token updated
  useEffect(() => {
    // Check localStorage for token on component mount and when auth changes
    const token = localStorage.getItem('googleAccessToken');
    console.log("Token from localStorage:", token ? "Found (length: " + token.length + ")" : "Not found");
    setLocalToken(token);
  }, [currentUser]);
  
  // Use the conversation hook
  const conversation = useConversation({
    onConnect: () => {
      console.log('Connected to agent')
      setError(null)
      // Clear messages when starting a new conversation
      setMessages([])
      messagesRef.current = []
    },
    onDisconnect: () => {
      console.log('Disconnected from agent')
      setShowTranscript(true)
      
      // Log the current messages
      console.log('onDisconnect handler called, processing transcript')
      console.log('Messages in state:', messages.length)
      console.log('Messages in ref:', messagesRef.current.length)
      
      // Always process the transcript directly
      if (messagesRef.current.length > 0) {
        // Deduplicate messages before processing
        const uniqueMessages = deduplicateMessages(messagesRef.current)
        processTranscriptDirectly(uniqueMessages)
      }
    },
    onMessage: (message) => {
      console.log('Message received:', message)
      
      // Extract the text and role from the message
      const messageText = message?.text || message?.message || ''
      const messageRole = message?.role || message?.source || 'unknown'
      
      if (messageText) {
        // Create the new message object
        const newMessage = { role: messageRole, text: messageText }
        
        // Check if this is a duplicate message (same text and role as the last message)
        const isDuplicate = messagesRef.current.length > 0 && 
          messagesRef.current[messagesRef.current.length - 1].text === messageText &&
          messagesRef.current[messagesRef.current.length - 1].role === messageRole;
        
        if (!isDuplicate) {
          console.log('Adding message to state and ref:', newMessage)
          
          // Update the state
          setMessages(prevMessages => {
            const updatedMessages = [...prevMessages, newMessage]
            return updatedMessages
          })
          
          // Update the ref directly
          messagesRef.current.push(newMessage)
        } else {
          console.log('Skipping duplicate message:', newMessage)
        }
      }
    },
    onError: (error) => {
      console.error('Conversation error:', error)
      setError(`Error: ${error.message || 'Unknown error'}`)
    },
  })
  
  // Helper function to deduplicate messages
  const deduplicateMessages = (messages) => {
    const uniqueMessages = [];
    const seen = new Set();
    
    for (const message of messages) {
      // Create a unique key for each message
      const key = `${message.role}:${message.text}`;
      
      if (!seen.has(key)) {
        seen.add(key);
        uniqueMessages.push(message);
      }
    }
    
    console.log(`Deduplicated ${messages.length} messages to ${uniqueMessages.length} unique messages`);
    return uniqueMessages;
  };
  
  // Start the conversation with availability data
  const startConversation = useCallback(async () => {
    try {
      setError(null)
      setMessages([])
      setShowTranscript(false)
      
      // Request microphone permission
      console.log('Requesting microphone permission...')
      await navigator.mediaDevices.getUserMedia({ audio: true })
      console.log('Microphone permission granted')
      
      // Start the conversation session
      console.log('Starting conversation with agent ID:', AGENT_ID)
      await conversation.startSession({
        agentId: AGENT_ID,
        dynamicVariables: {
          username: currentUser?.displayName || "User",
          current_time_iso: new Date().toISOString(),
          current_day: new Date().toLocaleDateString('en-US', { weekday: 'long' }),
          timezone_info: Intl.DateTimeFormat().resolvedOptions().timeZone,
          available_time: userAvailability || "Mon-Fri: 9am-5pm" // Default if not set
        }
      })
    } catch (error) {
      console.error('Failed to start conversation:', error)
      setError(`Failed to start conversation: ${error.message}`)
    }
  }, [conversation, currentUser, userAvailability])
  
  // End the conversation
  const stopConversation = useCallback(async () => {
    try {
      console.log('Ending conversation session...')
      
      // Log the current messages
      console.log('Current messages in state:', messages.length)
      console.log('Current messages in ref:', messagesRef.current.length)
      
      // Store a copy of the messages and deduplicate
      const currentMessages = deduplicateMessages([...messagesRef.current])
      
      // This should trigger the WebSocket to disconnect
      await conversation.endSession()
      
      // If onDisconnect isn't being called automatically, we can manually process the transcript here
      console.log('Manually processing transcript after ending session')
      console.log('Messages to process:', currentMessages.length)
      
      if (currentMessages.length > 0) {
        processTranscriptDirectly(currentMessages)
      }
    } catch (error) {
      console.error('Error ending conversation:', error)
      setError(`Error ending conversation: ${error.message}`)
      
      // Even if there's an error, try to process the transcript
      const currentMessages = deduplicateMessages([...messagesRef.current])
      if (currentMessages.length > 0) {
        processTranscriptDirectly(currentMessages)
      }
    }
  }, [conversation])
  
  // Process the transcript directly
  const processTranscriptDirectly = async (messagesToProcess = messages) => {
    try {
      console.log('Processing transcript directly')
      console.log('Messages to process:', messagesToProcess.length)
      
      // Format the transcript
      const transcript = messagesToProcess
        .map((msg) => `${msg.role === 'agent' ? 'Agent' : 'User'}: ${msg.text}`)
        .join('\n')
      
      console.log('Formatted transcript:', transcript)
      
      // Send the transcript to the backend
      const response = await fetch(`http://localhost:8000/api/process-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text_input: transcript }),
      })
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`)
      }
      
      const data = await response.json()
      console.log('API Response:', data)
      
      // Extract meeting data from the response
      if (data && data.meeting) {
        setMeetingData({
          title: data.meeting.title || '',
          startDateTime: data.meeting.startDateTime || '',
          endDateTime: data.meeting.endDateTime || '',
          description: data.meeting.description || ''
        })
      }
    } catch (error) {
      console.error('Error processing transcript:', error)
      setError(`Error processing transcript: ${error.message}`)
    }
  }
  
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
  
  // Format transcript for display
  const formattedTranscript = messages
    .map((msg) => `${msg.role === 'agent' ? 'Agent' : 'You'}: ${msg.text}`)
    .join('\n')
  
  // Watch for changes in conversation status
  useEffect(() => {
    // If the status changes from 'connected' to something else, process the transcript
    if (conversation.status !== 'connected' && messages.length > 0) {
      console.log('Conversation status changed to:', conversation.status)
      console.log('Processing transcript due to status change')
      processTranscriptDirectly()
    }
  }, [conversation.status, messages])
  
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
  
  // Update your addToCalendar function
  const addToCalendar = async () => {
    if (!meetingData.title) {
      setError("No meeting data to add to calendar");
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      // Get the token from localStorage
      const token = localStorage.getItem('googleAccessToken');
      if (!token) {
        setError("You need to sign in with Google to add events to your calendar");
        setLoading(false);
        return;
      }
      
      // Format the meeting data for Google Calendar
      const eventData = formatMeetingForCalendar(meetingData);
      console.log("Formatted event data:", eventData);
      
      // Create the event
      const result = await createEvent(token, 'primary', eventData);
      console.log("Event created:", result);
      
      // Show success state
      setCalendarSuccess(true);
      
      // Reset success state after 3 seconds
      setTimeout(() => {
        setCalendarSuccess(false);
      }, 3000);
      
    } catch (error) {
      console.error("Error adding to calendar:", error);
      setError(`Error adding to calendar: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Handle availability save
  const handleAvailabilitySave = (formattedAvailability) => {
    setUserAvailability(formattedAvailability);
    console.log('Availability saved:', formattedAvailability);
  };
  
  // Replace your existing testCalendarIntegration function with this simpler version
  const testCalendarIntegration = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Use fixed ISO 8601 dates for testing
      const dummyMeetingData = {
        title: 'Meeting with James Nguyen',
        start_time: '2023-07-10T15:00:00.000Z', // 3 PM on a Monday
        end_time: '2023-07-10T16:00:00.000Z',   // 4 PM on a Monday
        description: 'Medical appointment'
      };
      
      console.log('Testing calendar integration with dummy data:', dummyMeetingData);
      
      const response = await fetch('http://localhost:8000/api/test-calendar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          meeting_details: dummyMeetingData,
          host_email: currentUser.email,
          host_availability: userAvailability || "Mon-Fri: 9am-5pm"
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Calendar test result:', result);
      
      // Update meeting data in the UI
      setMeetingData({
        title: dummyMeetingData.title,
        startDateTime: dummyMeetingData.start_time,
        endDateTime: dummyMeetingData.end_time,
        description: dummyMeetingData.description
      });
      
      // Show success notification
      if (result.success) {
        setCalendarSuccess(true);
        setTimeout(() => {
          setCalendarSuccess(false);
        }, 3000);
      } else {
        setError(`Calendar test failed: ${result.error || 'Unknown error'}`);
      }
      
    } catch (error) {
      console.error('Error testing calendar integration:', error);
      setError(`Error testing calendar: ${error.message}`);
    } finally {
      setLoading(false);
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
              Talk to the AI agent to schedule a meeting
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
          {/* {userAvailability && (
            <div className="text-sm bg-gray-50 p-3 rounded-md border mb-6">
              <div className="font-medium mb-1 flex items-center">
                <span>Current Availability</span>
                <FiCheck className="ml-2 text-green-500" size={16} />
              </div>
              <div className="text-gray-600">{userAvailability}</div>
            </div>
          )} */}
          
          {/* Test Calendar Integration Button
          <div className="flex justify-center mt-4">
            <Button 
              onClick={testCalendarIntegration}
              variant="outline"
              className="flex items-center gap-2"
              disabled={loading}
            >
              <FiTool size={16} />
              Test Calendar Integration
            </Button>
          </div> */}
          
          {/* Phone Schedule Form - Now right after test button */}
          {userAvailability && <PhoneScheduleForm userAvailability={userAvailability} />}
          
          {/* Rest of your existing UI */}
          <div className="flex justify-center">
            <Button 
              onClick={conversation.status === 'connected' ? stopConversation : startConversation}
              variant={conversation.status === 'connected' ? "destructive" : "default"}
              className="flex items-center gap-2"
            >
              {conversation.status === 'connected' ? <FiPhoneOff size={16} /> : <FiPhone size={16} />}
              {conversation.status === 'connected' ? 'End Call' : 'Talk to Agent'}
            </Button>
          </div>
          
          {/* Connection Status */}
          <div className="text-center">
            <p className="text-sm">
              Status: <span className={conversation.status === 'connected' ? "text-green-600 font-medium" : "text-gray-500"}>
                {conversation.status === 'connected' ? 'Connected' : 'Disconnected'}
              </span>
            </p>
            {conversation.status === 'connected' && (
              <p className="text-sm">
                Agent is <span className="font-medium">
                  {conversation.isSpeaking ? 'speaking' : 'listening'}
                </span>
              </p>
            )}
          </div>
          
          {/* Transcript Display */}
          {/* {showTranscript && messages.length > 0 && (
            <div className="mt-4 p-4 border rounded-lg bg-gray-50">
              <h3 className="text-md font-medium mb-2">Conversation Transcript</h3>
              <pre className="whitespace-pre-line text-sm bg-white p-3 rounded border max-h-40 overflow-y-auto">
                {formattedTranscript}
              </pre>
            </div>
          )} */}
          
          {/* Meeting Data Form */}
          <div className="mt-6 p-4 border rounded-lg bg-gray-50">
            <h3 className="text-lg font-medium mb-4 flex items-center">
              <FiCalendar className="mr-2" size={18} />
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
            </div>
            
            <Button
              onClick={addToCalendar}
              disabled={!meetingData.title || !localStorage.getItem('googleAccessToken') || loading || calendarSuccess}
              className={`mt-4 w-full flex items-center justify-center gap-2 ${
                calendarSuccess ? 'bg-green-600 hover:bg-green-700' : ''
              }`}
            >
              {calendarSuccess ? (
                <>
                  <FiCheck size={16} />
                  Meeting Added!
                </>
              ) : (
                <>
                  <FiCalendar size={16} />
                  Add to Google Calendar
                </>
              )}
            </Button>
          </div>
          
          {error && <p className="text-red-500 text-center">{error}</p>}
        </CardContent>
      </Card>
    </div>
  );
}

export default App; 