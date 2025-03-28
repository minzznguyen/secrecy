// Import the functions you need from the SDKs you need
import { initializeApp, getApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

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

// Log the configuration (without sensitive data)
console.log("Firebase Config:", {
  projectId: firebaseConfig.projectId,
  authDomain: firebaseConfig.authDomain,
  storageBucket: firebaseConfig.storageBucket
});

// Initialize Firebase
const app = initializeApp(firebaseConfig);
console.log("Firebase app initialized successfully");

// Initialize Analytics only in production
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
console.log("Firebase Auth initialized successfully");

// Initialize Firestore
const db = getFirestore(app);
console.log("Firestore initialized successfully");

// Create Google provider
const googleProvider = new GoogleAuthProvider();

// Add Google scopes - using most specific scopes needed
googleProvider.addScope('https://www.googleapis.com/auth/userinfo.email');
googleProvider.addScope('https://www.googleapis.com/auth/userinfo.profile');
googleProvider.addScope('https://www.googleapis.com/auth/calendar.events');  // This includes both read and write access to events

// Configure provider to request refresh tokens
googleProvider.setCustomParameters({
  prompt: 'consent',
  access_type: 'offline',
  response_type: 'code'
});

// Initialize Google Auth
const googleAuth = getAuth(app);

console.log("Firebase auth initialized with Google scopes");

export { auth, googleAuth, googleProvider, db };
export default app;
