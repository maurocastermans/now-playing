from spotipy import SpotifyOAuth

# Run this once on your desktop/laptop to obtain an access token
# Afterwards, copy the .cache file to your Raspberry Pi.
# Spotipy will from then on automatically refresh the access token using the refresh token

SPOTIFY_CLIENT_ID = "<client_id>"
SPOTIFY_CLIENT_SECRET = "<client_secret>"
SPOTIFY_REDIRECT_URI = "http://localhost:8888/callback"
SPOTIFY_SCOPE = "playlist-modify-public playlist-modify-private"

auth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SPOTIFY_SCOPE,
    open_browser=True
)

token_info = auth.get_access_token(as_dict=False)
print("Access token successfully retrieved and cached in .cache file.")