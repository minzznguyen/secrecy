import { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { auth } from '../lib/firebase';

const AuthContext = createContext();

// Store token in localStorage for persistence
const saveTokenToStorage = (token) => {
  if (token) {
    localStorage.setItem('googleAccessToken', token);
  } else {
    localStorage.removeItem('googleAccessToken');
  }
};

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  // Initialize from localStorage if available
  const [googleAccessToken, setGoogleAccessToken] = useState(
    localStorage.getItem('googleAccessToken')
  );

  useEffect(() => {
    console.log("Setting up auth state listener");
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      console.log("Auth state changed:", user ? "User logged in" : "No user");
      setCurrentUser(user);
      
      // If user logs out, clear token
      if (!user) {
        console.log("User logged out, clearing token");
        setGoogleAccessToken(null);
        saveTokenToStorage(null);
      }
      
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Function to store Google access token
  const setGoogleToken = (token) => {
    console.log("Storing Google access token:", token ? "Token received" : "No token");
    setGoogleAccessToken(token);
    saveTokenToStorage(token);
  };

  // Add a function to refresh the token when needed
  const refreshGoogleToken = async () => {
    try {
      const user = auth.currentUser;
      if (user) {
        const provider = new GoogleAuthProvider();
        provider.addScope('https://www.googleapis.com/auth/calendar');
        provider.addScope('https://www.googleapis.com/auth/calendar.events');
        
        const result = await signInWithPopup(auth, provider);
        const credential = GoogleAuthProvider.credentialFromResult(result);
        const newToken = credential.accessToken;
        
        console.log("Token refreshed:", newToken ? "Success" : "Failed");
        setGoogleToken(newToken);
        return newToken;
      }
    } catch (error) {
      console.error('Error refreshing token:', error);
      throw error;
    }
  };

  const value = {
    currentUser,
    loading,
    googleAccessToken,
    setGoogleToken,
    refreshGoogleToken
  };

  // Show a loading indicator while checking auth state
  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
} 