import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional
import logging

import sys
sys.path.append("..")
from logger import Logger
from config import Config

class SpotifyService:
    def __init__(self):
        self._logger: logging.Logger = Logger().get_logger()
        self._config: dict = Config().get_config()
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self._config['spotify']['client_id'],
            client_secret=self._config['spotify']['client_secret'],
            redirect_uri="http://localhost:8888/callback",
            scope="playlist-modify-public playlist-modify-private",
            open_browser=False  # Important for headless mode
        ))

    def search_track_uri(self, title: str, artist: str) -> Optional[str]:
        query = f"track:{title} artist:{artist}"
        results = self.sp.search(q=query, type="track", limit=1)
        tracks = results.get('tracks', {}).get('items', [])
        if tracks:
            return tracks[0]['uri']
        self._logger.debug("Track not found on Spotify.")
        return None

    def add_to_playlist(self, track_uri: str) -> None:
        self.sp.playlist_add_items(self._config['spotify']['playlist_id'], [track_uri])
        self._logger.info(f"Added track '{track_uri}' to playlist.")
