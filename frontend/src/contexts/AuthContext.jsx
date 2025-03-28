import { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, GoogleAuthProvider, signInWithPopup } from 'firebase/auth';
import { auth } from '../lib/firebase';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [googleAccessToken, setGoogleAccessToken] = useState(null);
  const [googleRefreshToken, setGoogleRefreshToken] = useState(null);

  useEffect(() => {
    console.log("Setting up auth state listener");
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      console.log("Auth state changed:", user ? "User logged in" : "No user");
      setCurrentUser(user);
      
      // If user logs out, clear tokens
      if (!user) {
        console.log("User logged out, clearing tokens");
        setGoogleAccessToken(null);
        setGoogleRefreshToken(null);
      }
      
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  // Function to store Google tokens
  const setGoogleTokens = (accessToken, refreshToken) => {
    console.log("Storing Google tokens:", accessToken ? "Access token received" : "No access token", refreshToken ? "Refresh token received" : "No refresh token");
    setGoogleAccessToken(accessToken);
    setGoogleRefreshToken(refreshToken);
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
        const newAccessToken = credential.accessToken;
        const newRefreshToken = credential.refreshToken;
        
        console.log("Tokens refreshed:", newAccessToken ? "Access token success" : "Failed", newRefreshToken ? "Refresh token success" : "Failed");
        setGoogleTokens(newAccessToken, newRefreshToken);
        return newAccessToken;
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
    googleRefreshToken,
    setGoogleTokens,
    refreshGoogleToken,
    setCurrentUser
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