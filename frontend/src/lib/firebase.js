// Import the functions you need from the SDKs you need
import { initializeApp, getApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

// Initialize Firebase using try-catch to handle existing app
let app;
try {
  app = getApp();
} catch (e) {
  app = initializeApp(firebaseConfig);
}

// Initialize Analytics only in production and if supported
let analytics = null;
if (import.meta.env.PROD) {
  try {
    analytics = getAnalytics(app);
    console.log("Firebase Analytics initialized successfully");
  } catch (e) {
    console.log("Firebase Analytics initialization skipped");
  }
}

// Initialize Firebase Authentication
const auth = getAuth(app);

// Create Google provider with calendar scopes
const googleProvider = new GoogleAuthProvider();

// Add Google Calendar scopes
googleProvider.addScope('https://www.googleapis.com/auth/calendar');
googleProvider.addScope('https://www.googleapis.com/auth/calendar.events');

// Set custom parameters
googleProvider.setCustomParameters({
  prompt: 'consent',
  access_type: 'offline'
});

console.log("Firebase auth initialized with Google Calendar scopes");

export { auth, googleProvider };
export default app;
