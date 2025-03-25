import { useState } from 'react';
import { signInWithEmailAndPassword, signInWithPopup } from 'firebase/auth';
import { auth, googleProvider } from '../../lib/firebase';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '../ui/card';
import { FcGoogle } from 'react-icons/fc';
import { useAuth } from '../../contexts/AuthContext';
import { GoogleAuthProvider } from 'firebase/auth';

export function SignIn({ onSignIn }) {
  const { setGoogleToken } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleEmailSignIn = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      console.log('User signed in:', userCredential.user);
      if (onSignIn) onSignIn(userCredential.user);
    } catch (error) {
      console.error('Error signing in:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log("Starting Google sign-in process");
      
      // Create a new provider instance for this sign-in to ensure fresh scopes
      const provider = new GoogleAuthProvider();
      
      // Add the specific scopes needed for calendar
      provider.addScope('https://www.googleapis.com/auth/calendar');
      provider.addScope('https://www.googleapis.com/auth/calendar.events');
      
      // Force re-authentication to get fresh tokens with the right scopes
      provider.setCustomParameters({
        prompt: 'consent',
        access_type: 'offline'
      });
      
      const userCredential = await signInWithPopup(auth, provider);
      console.log('User signed in with Google:', userCredential.user.email);
      
      // Get the credential from the result
      const credential = GoogleAuthProvider.credentialFromResult(userCredential);
      console.log("Credential received:", credential ? "Yes" : "No");
      
      if (credential) {
        // This is the Google OAuth access token we need for API calls
        const token = credential.accessToken;
        console.log('Access token received:', token ? "Yes (length: " + token.length + ")" : "No");
        
        if (token) {
          console.log('Setting Google token in context');
          setGoogleToken(token);
          
          // Store it in localStorage directly as a backup
          localStorage.setItem('googleAccessToken', token);
          
          // Verify token was stored
          setTimeout(() => {
            const storedToken = localStorage.getItem('googleAccessToken');
            console.log("Token in localStorage:", storedToken ? "Yes (length: " + storedToken.length + ")" : "No");
          }, 100);
        } else {
          console.error('No access token received from Google');
          setError("Failed to get access token from Google");
        }
      } else {
        console.error('No credential received from Google sign-in');
        setError("Failed to get credentials from Google");
      }
      
      if (onSignIn) onSignIn(userCredential.user);
    } catch (error) {
      console.error('Error signing in with Google:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Sign In</CardTitle>
        <CardDescription>Sign in to your account to continue</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleEmailSignIn} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
            />
          </div>
          
          {error && <p className="text-red-500 text-sm">{error}</p>}
          
          <Button 
            type="submit" 
            className="w-full" 
            disabled={loading}
          >
            {loading ? 'Signing in...' : 'Sign In with Email'}
          </Button>
          
          <div className="relative my-4">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or</span>
            </div>
          </div>
          
          <Button 
            type="button" 
            variant="outline" 
            className="w-full flex items-center justify-center gap-2"
            onClick={handleGoogleSignIn}
            disabled={loading}
          >
            <FcGoogle size={20} />
            Sign In with Google
          </Button>
          
          <div className="mt-2 text-xs text-gray-500 text-center">
            Signing in with Google will request access to your Google Calendar to schedule meetings.
          </div>
        </form>
      </CardContent>
    </Card>
  );
} 