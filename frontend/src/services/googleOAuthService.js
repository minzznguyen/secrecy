// Google OAuth service for direct token handling

const GOOGLE_OAUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth';
const GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token';
const REDIRECT_URI = `${window.location.origin}/oauth/callback`;

// Scopes needed for calendar access
const SCOPES = [
  'https://www.googleapis.com/auth/userinfo.email',
  'https://www.googleapis.com/auth/userinfo.profile',
  'https://www.googleapis.com/auth/calendar.events'
].join(' ');

export const initiateGoogleOAuth = () => {
  const params = new URLSearchParams({
    client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: 'code',
    scope: SCOPES,
    access_type: 'offline',
    prompt: 'consent'
  });

  // Store state for verification
  const state = Math.random().toString(36).substring(7);
  sessionStorage.setItem('oauth_state', state); // Using sessionStorage for temporary state
  params.append('state', state);

  // Redirect to Google OAuth
  window.location.href = `${GOOGLE_OAUTH_URL}?${params.toString()}`;
};

export const handleOAuthCallback = async (code, state) => {
  try {
    console.log('Starting OAuth callback with code:', code);
    console.log('State:', state);
    
    // Verify state
    const savedState = sessionStorage.getItem('oauth_state');
    if (state !== savedState) {
      console.error('State mismatch:', { received: state, saved: savedState });
      throw new Error('Invalid state parameter');
    }

    // Clear state after verification
    sessionStorage.removeItem('oauth_state');
    
    const response = await fetch(GOOGLE_TOKEN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        code,
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        client_secret: import.meta.env.VITE_GOOGLE_CLIENT_SECRET,
        redirect_uri: REDIRECT_URI,
        grant_type: 'authorization_code'
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Token exchange failed:', errorData);
      throw new Error(`Failed to exchange code for tokens: ${errorData.error_description || errorData.error}`);
    }

    const data = await response.json();
    console.log('Token exchange response:', {
      access_token: data.access_token ? 'Received' : 'Missing',
      refresh_token: data.refresh_token ? 'Received' : 'Missing',
      expires_in: data.expires_in,
      scope: data.scope,
      token_type: data.token_type
    });

    if (!data.refresh_token) {
      console.warn('No refresh token received in response');
    }

    return data;
  } catch (error) {
    console.error('Error in handleOAuthCallback:', error);
    throw error;
  }
};

export const refreshAccessToken = async (refreshToken) => {
  try {
    const response = await fetch(GOOGLE_TOKEN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
        client_secret: import.meta.env.VITE_GOOGLE_CLIENT_SECRET,
        refresh_token: refreshToken,
        grant_type: 'refresh_token'
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error_description || 'Failed to refresh token');
    }

    const data = await response.json();
    return data.access_token;
  } catch (error) {
    console.error('Error refreshing token:', error);
    throw error;
  }
}; 