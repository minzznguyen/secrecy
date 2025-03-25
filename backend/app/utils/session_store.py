class SessionStore:
    def __init__(self):
        self.sessions = {}
        
    def store_session_data(self, session_id, data):
        """Store data for a session"""
        self.sessions[session_id] = data
        print(f"\n=== SESSION STORE: STORED DATA ===")
        print(f"Session ID: {session_id}")
        print(f"Data: {data}")
        print(f"==================================\n")
        
    def get_session_data(self, session_id):
        """Get data for a session"""
        data = self.sessions.get(session_id)
        print(f"\n=== SESSION STORE: RETRIEVED DATA ===")
        print(f"Session ID: {session_id}")
        print(f"Data: {data}")
        print(f"=====================================\n")
        return data
        
    def remove_session_data(self, session_id):
        """Remove data for a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"\n=== SESSION STORE: REMOVED DATA ===")
            print(f"Session ID: {session_id}")
            print(f"===================================\n") 