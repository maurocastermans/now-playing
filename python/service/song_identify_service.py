import asyncio
import logging
from typing import Optional, Dict, Any
import requests
import io
from shazamio import Shazam
from ..logger import Logger

class SongIdentifyService:
    def __init__(self) -> None:
        self.logger = Logger().get_logger()
        self.shazam = Shazam()

    def identify(self, audio_wav_buffer: io.BytesIO) -> Optional[Dict[str, Any]]:
        try:
            result = asyncio.run(self.shazam.recognize(audio_wav_buffer.read()))
            if not result or "track" not in result:
                logger.info("No song identified in the provided audio buffer.")
                return None
            return self._parse_result(result)
        except Exception as ex:
            logger.error(f"Error identifying song: {ex}")
            return None

    @staticmethod
    def _parse_result(result: Optional[Dict]) -> Optional[Dict[str, Any]]:
        track = result["track"]
        return {
            "title": track.get("title", "Unknown"),
            "artist": track.get("subtitle", "Unknown"),
            "album": SongIdentifyService._extract_album_name(track),
            "album_art": track.get("images", {}).get("coverart", "Unknown"),
            "offset": SongIdentifyService._extract_offset(result),
            "song_duration": SongIdentifyService._fetch_duration(track.get("isrc", "Unknown")),
        }

    @staticmethod
    def _extract_album_name(track: Dict) -> str:
        metadata = track.get("sections", [{}])[0].get("metadata", [])
        for item in metadata:
            if item.get("title") == "Album":
                return item.get("text", "Unknown")
        return "Unknown"

    @staticmethod
    def _extract_offset(result: Dict) -> str:
        matches = result.get("matches", [{}])
        return matches[0].get("offset", "Unknown") if matches else "Unknown"

    @staticmethod
    def _fetch_duration(isrc: str) -> Optional[float]:
        url = f"https://musicbrainz.org/ws/2/recording/?query=isrc:{isrc}&fmt=json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return SongIdentifyService._parse_duration(response.json())
        except requests.exceptions.RequestException as ex:
            logger.error(f"Error fetching song duration from MusicBrainz: {ex}")
            return None

    @staticmethod
    def _parse_duration(data: Dict) -> Optional[float]:
        recordings = data.get("recordings", [])
        if not recordings:
            logger.info("No recordings found in MusicBrainz response.")
            return None

        duration_ms = recordings[0].get("length")
        return duration_ms / 1000 if duration_ms else None
