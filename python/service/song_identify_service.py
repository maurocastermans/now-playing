import asyncio
from typing import Optional, Dict, Any
import requests
import io
from shazamio import Shazam
from dataclasses import dataclass

import sys
sys.path.append("..")
from logger import Logger

@dataclass(frozen=True)
class SongInfo:
    title: Optional[str]
    artist: Optional[str]
    album: Optional[str]
    album_art: Optional[str]
    offset: Optional[float]
    song_duration: Optional[float]

class SongIdentifyService:
    def __init__(self) -> None:
        self._logger = Logger().get_logger()
        self._shazam = Shazam()

    def identify(self, audio_wav_buffer: io.BytesIO) -> Optional[SongInfo]:
        try:
            result = asyncio.run(self._shazam.recognize(audio_wav_buffer.read()))
            if not result or "track" not in result:
                self._logger.info("No song identified in the provided audio buffer.")
                return None
            self._logger.info("Song identified in the provided audio buffer.")
            return self._parse_result(result)
        except Exception as ex:
            self._logger.error(f"Error identifying song: {ex}")
            return None

    def _parse_result(self, result: Optional[Dict]) -> SongInfo:
        track = result["track"]
        return SongInfo(
            title=track.get("title", None),
            artist=track.get("subtitle", None),
            album=self._extract_album_name(track),
            album_art=track.get("images", {}).get("coverart", None),
            offset=self._extract_offset(result),
            song_duration=self._fetch_duration(track.get("isrc", None)),
        )

    @staticmethod
    def _extract_album_name(track: Dict) -> Optional[str]:
        metadata = track.get("sections", [{}])[0].get("metadata", [])
        for item in metadata:
            if item.get("title") == "Album":
                return item.get("text", None)
        return None

    @staticmethod
    def _extract_offset(result: Dict) -> Optional[float]:
        matches = result.get("matches", [{}])
        return matches[0].get("offset", None) if matches else None


    def _fetch_duration(self, isrc: str) -> Optional[float]:
        url = f"https://musicbrainz.org/ws/2/recording/?query=isrc:{isrc}&fmt=json"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return self._parse_duration(response.json())
        except requests.exceptions.RequestException as ex:
            self._logger.error(f"Error fetching song duration from MusicBrainz: {ex}")
            return None

    def _parse_duration(self, data: Dict) -> Optional[float]:
        recordings = data.get("recordings", [])
        if not recordings:
            self._logger.info("No recordings found in MusicBrainz response.")
            return None

        duration_ms = recordings[0].get("length")
        return duration_ms / 1000 if duration_ms else None
