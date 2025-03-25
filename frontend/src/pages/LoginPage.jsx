import { useState } from 'react';
import { SignIn } from '../components/auth/SignIn';
import { SignUp } from '../components/auth/SignUp';
import { createUserWithEmailAndPassword, updateProfile } from 'firebase/auth';
import { auth } from '../lib/firebase';

export function LoginPage() {
  const [authMode, setAuthMode] = useState('signin');
  const [name, setName] = useState('');
  
  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    
    try {
      // Create user with email and password
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      
      // Update the user's profile with their name
      await updateProfile(userCredential.user, {
        displayName: name
      });
      
      // Refresh the user to get the updated profile
      await userCredential.user.reload();
      
      console.log("User signed up successfully with name:", name);
    } catch (error) {
      setError(error.message);
      console.error("Error signing up:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 max-w-md">
      <h1 className="text-3xl font-bold text-center mb-6">Meeting Scheduler</h1>
      
      {authMode === 'signin' ? (
        <>
          <SignIn onSignIn={() => {}} />
          <p className="text-center mt-4">
            Don't have an account?{' '}
            <button 
              className="text-blue-500 hover:underline" 
              onClick={() => setAuthMode('signup')}
            >
              Sign Up
            </button>
          </p>
        </>
      ) : (
        <>
          <SignUp onSignUp={() => setAuthMode('signin')} />
          <p className="text-center mt-4">
            Already have an account?{' '}
            <button 
              className="text-blue-500 hover:underline" 
              onClick={() => setAuthMode('signin')}
            >
              Sign In
            </button>
          </p>
        </>
      )}

      {authMode === 'signup' && (
        <div className="mb-4">
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Full Name
          </label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            required
          />
        </div>
      )}
    </div>
  );
} 