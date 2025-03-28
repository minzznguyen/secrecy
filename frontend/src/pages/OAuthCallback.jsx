import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { signInWithCredential, GoogleAuthProvider } from 'firebase/auth';
import { useAuth } from '../contexts/AuthContext';
import { auth, db } from '../lib/firebase';
import { doc, setDoc } from 'firebase/firestore';

export function OAuthCallback() {
  const navigate = useNavigate();
  const { setGoogleTokens } = useAuth();
  
  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get the authorization code from the URL
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        const state = urlParams.get('state');
        
        if (!code) {
          console.error('No authorization code found in URL');
          navigate('/');
          return;
        }
        
        // Exchange code for tokens
        const response = await fetch('https://oauth2.googleapis.com/token', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({
            code,
            client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
            client_secret: import.meta.env.VITE_GOOGLE_CLIENT_SECRET,
            redirect_uri: `${window.location.origin}/oauth/callback`,
            grant_type: 'authorization_code'
          })
        });
        
        if (!response.ok) {
          throw new Error('Failed to exchange code for tokens');
        }
        
        const data = await response.json();
        
        // Create Google credential
        const credential = GoogleAuthProvider.credential(null, data.access_token);
        
        // Sign in with credential
        const userCredential = await signInWithCredential(auth, credential);
        const userEmail = userCredential.user.email;
        
        // Store tokens in Firestore
        console.log('Preparing to store tokens in Firestore for user:', userEmail);
        
        const tokens = {
          access_token: data.access_token,
          refresh_token: data.refresh_token,
          token_expiry: Date.now() + (data.expires_in * 1000),
          updated_at: new Date().toISOString()
        };
        
        // Update context
        setGoogleTokens(data.access_token, data.refresh_token);
        
        // Store in Firestore using email as document ID
        const userDoc = doc(db, 'user_tokens', userEmail);
        await setDoc(userDoc, tokens, { merge: true });
        
        console.log('Tokens successfully stored in Firestore');
        
        // Redirect back to home
        navigate('/');
        
      } catch (error) {
        console.error('Error in OAuth callback:', error);
        navigate('/');
      }
    };
    
    handleCallback();
  }, [navigate, setGoogleTokens]);
  
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="text-center">
        <h2 className="text-xl font-semibold mb-4">Processing OAuth Callback</h2>
        <p>Please wait while we complete the authentication process...</p>
      </div>
    </div>
  );
} 