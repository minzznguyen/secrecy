from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class CallManager:
    """Manages active calls and their transcripts"""
    
    def __init__(self):
        self.active_calls: Dict[str, Dict] = {}
        self.call_params: Dict[str, Dict] = {}
        self.pending_params = {}  # New dictionary to store parameters before the call
    
    def register_call(self, call_sid: str, host_availability: Optional[str] = None, host_email: Optional[str] = None):
        """Register a new call"""
        logger.info(f"Registering call with SID: {call_sid}")
        self.active_calls[call_sid] = {
            "transcript": [],
            "host_availability": host_availability,
            "host_email": host_email,
            "conversation_id": None
        }
    
    def set_conversation_id(self, call_sid: str, conversation_id: str):
        """Set the ElevenLabs conversation ID for a call"""
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["conversation_id"] = conversation_id
            logger.info(f"Set conversation ID {conversation_id} for call {call_sid}")
    
    def add_transcript_entry(self, call_sid: str, role: str, content: str):
        """Add an entry to the call transcript"""
        if call_sid in self.active_calls:
            self.active_calls[call_sid]["transcript"].append({
                "role": role,
                "content": content
            })
            logger.debug(f"Added {role} transcript for call {call_sid}: {content}")
    
    def get_call_data(self, call_sid: str) -> Optional[Dict]:
        """Get data for a specific call"""
        return self.active_calls.get(call_sid)
    
    def get_transcript(self, call_sid: str) -> List[Dict]:
        """Get the full transcript for a call"""
        if call_sid in self.active_calls:
            return self.active_calls[call_sid]["transcript"]
        return []
    
    def get_formatted_transcript(self, call_sid: str) -> str:
        """Get a formatted string of the transcript"""
        if call_sid in self.active_calls:
            transcript_entries = self.active_calls[call_sid]["transcript"]
            
            if not transcript_entries:
                logger.warning(f"No transcript entries found for call {call_sid}")
                return ""
            
            logger.info(f"Found {len(transcript_entries)} transcript entries for call {call_sid}")
            
            formatted = "\n".join([f"{entry['role'].capitalize()}: {entry['content']}" for entry in transcript_entries])
            
            # Log preview of transcript
            preview = formatted[:200] + "..." if len(formatted) > 200 else formatted
            logger.info(f"Formatted transcript preview: {preview}")
            
            return formatted
        
        logger.warning(f"No call data found for SID: {call_sid}")
        return ""
    
    def remove_call(self, call_sid: str):
        """Remove a call from tracking"""
        if call_sid in self.active_calls:
            logger.info(f"Removing call with SID: {call_sid}")
            del self.active_calls[call_sid]
    
    def store_call_params(self, call_sid, params):
        """Store parameters for a call before it's made"""
        self.call_params[call_sid] = params
        print(f"\n=== CALL MANAGER: STORED PARAMETERS ===")
        print(f"Call SID: {call_sid}")
        print(f"Parameters: {params}")
        print(f"======================================\n")
    
    def get_call_params(self, call_sid):
        """Get parameters for a call"""
        params = self.call_params.get(call_sid)
        print(f"\n=== CALL MANAGER: RETRIEVED PARAMETERS ===")
        print(f"Call SID: {call_sid}")
        print(f"Parameters: {params}")
        print(f"=========================================\n")
        return params
    
    def store_pending_params(self, call_sid, availability, host_email, host_name=None):
        """Store parameters for a call before it's connected to WebSocket"""
        self.pending_params[call_sid] = {
            "availability": availability,
            "host_email": host_email,
            "host_name": host_name
        }
        print(f"\n=== CALL MANAGER: STORED PENDING PARAMETERS ===")
        print(f"Call SID: {call_sid}")
        print(f"Availability: {availability}")
        print(f"Host Email: {host_email}")
        print(f"Host Name: {host_name}")
        print(f"==============================================\n")
        
    def get_pending_params(self, call_sid):
        """Get pending parameters for a call"""
        return self.pending_params.get(call_sid)
    
    def register_call_with_name(self, call_sid: str, host_availability: Optional[str] = None, 
                               host_email: Optional[str] = None, host_name: Optional[str] = None):
        """Register a new call with host name"""
        logger.info(f"Registering call with SID: {call_sid}")
        self.active_calls[call_sid] = {
            "transcript": [],
            "host_availability": host_availability,
            "host_email": host_email,
            "host_name": host_name,
            "conversation_id": None
        }
        print(f"\n=== CALL MANAGER: REGISTERED CALL WITH NAME ===")
        print(f"Call SID: {call_sid}")
        print(f"Host Availability: {host_availability}")
        print(f"Host Email: {host_email}")
        print(f"Host Name: {host_name}")
        print(f"==============================================\n") 