import asyncio
import logging
from typing import Optional, Dict, Any
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


class SongIdentifyService:
    def __init__(self) -> None:
        self._logger: logging.Logger = Logger().get_logger()
        self._shazam: Shazam = Shazam()

    def identify(self, audio_wav_buffer: io.BytesIO) -> Optional[SongInfo]:
        try:
            result = asyncio.run(self._shazam.recognize(audio_wav_buffer.read()))
            if not result or "track" not in result:
                self._logger.info("No song identified in the provided audio buffer.")
                return None
            self._logger.info("Song identified in the provided audio buffer.")
            return SongIdentifyService._parse_result(result)
        except Exception as ex:
            self._logger.error(f"Error identifying song: {ex}")
            return None

    @staticmethod
    def _parse_result(result: Optional[Dict]) -> SongInfo:
        track = result['track']
        return SongInfo(
            title=track.get('title', None),
            artist=track.get('subtitle', None),
            album=SongIdentifyService._extract_album_name(track),
            album_art=track.get('images', {}).get('coverart', None)
        )

    @staticmethod
    def _extract_album_name(track: Dict) -> Optional[str]:
        metadata = track.get('sections', [{}])[0].get('metadata', [])
        for item in metadata:
            if item.get('title') == 'Album':
                return item.get('text', None)
        return None
