from flask import Flask, request, jsonify, redirect, session, url_for
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Debug: Print environment variables
print("SPOTIFY_CLIENT_ID:", os.getenv('SPOTIFY_CLIENT_ID'))
print("SPOTIFY_CLIENT_SECRET:", os.getenv('SPOTIFY_CLIENT_SECRET'))

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure session key

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'  # Ensure this matches your Spotify Developer Dashboard

# Initialize Spotipy client
sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-read-private user-read-email user-library-read user-read-playback-state"
)

# Home route - redirects to Spotify login
@app.route('/')
def home():
    auth_url = sp_oauth.get_authorize_url()
    print(f"[DEBUG] Authorization URL: {auth_url}")  # Print auth URL for manual testing
    return redirect(auth_url)

# Callback route
@app.route('/callback')
def callback():
    error = request.args.get('error')
    if error:
        return f"Error from Spotify: {error}", 400  # Handle 'access_denied' errors

    code = request.args.get('code')
    if not code:
        return "Error: No code returned from Spotify", 400  # Debugging step

    try:
        # Clear previous session token (if any)
        session.pop('token_info', None)

        # Request access token (Updated method)
        token_info = sp_oauth.get_access_token(code)  # Fix deprecation warning

        session['token_info'] = token_info  # Store token in session
        print(f"[DEBUG] Access Token: {token_info}")  # Debugging step

        return jsonify({"access_token": token_info})
    except Exception as e:
        return f"Error retrieving access token: {str(e)}", 500

# Get current user's playlists
@app.route('/playlists', methods=['GET'])
def get_playlists():
    try:
        token_info = session.get('token_info', None)
        if not token_info:
            return redirect(url_for('home'))  # Redirect to login if no token

        sp = spotipy.Spotify(auth=token_info['access_token'])
        playlists = sp.current_user_playlists()
        return jsonify(playlists)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Play a song
@app.route('/play_song', methods=['POST'])
def play_song():
    try:
        token_info = session.get('token_info', None)
        if not token_info:
            return redirect(url_for('home'))  # Re-authenticate if no token

        sp = spotipy.Spotify(auth=token_info['access_token'])
        song_uri = request.json.get('song_uri')  # Expecting song URI in the request body
        sp.start_playback(uris=[song_uri])
        return jsonify({"message": "Song is now playing!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)