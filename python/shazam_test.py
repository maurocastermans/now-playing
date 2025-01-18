import asyncio
import logging

import requests
from shazamio import Shazam, Serialize

logger = logging.getLogger("now_playing_logger")

class ShazamService:
    def __init__(self):
        self.shazam = Shazam()

    async def _recognize_song(self, audio_wav_buffer):
        return await self.shazam.recognize(audio_wav_buffer)

    def identify_song(self, audio_wav_buffer):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self._recognize_song(audio_wav_buffer))
            serialized = Serialize.full_track(result)
            print(serialized)
            if result and 'track' in result:
                print("hallo")
            #     track = result['track']
            #     album_art = track.get('images', {}).get('coverart', 'No cover art available')
            #     isrc = track.get('isrc', {})
            #     offset = result['matches'][0].get('offset', {})
            #     song_duration = fetch_song_duration(isrc)
            #     return {
            #         'title': track.get('title', 'Unknown'),
            #         'artist': track.get('subtitle', 'Unknown'),
            #         'album': next((item['text'] for item in track.get('sections', [{}])[0].get('metadata', []) if
            #                        item.get('title') == 'Album'), 'Unknown'),
            #         'album_art': album_art,
            #         'offset': offset,
            #         'song_duration': song_duration
            #     }
            else:
                return None
        except Exception as ex:
            logger.error(ex)
        finally:
            loop.close()


def fetch_song_duration(isrc):
    # MusicBrainz API endpoint for ISRC
    url = f'https://musicbrainz.org/ws/2/recording/?query=isrc:{isrc}&fmt=json'
    try:
        response = requests.get(url)
        data = response.json()
        song_duration = data.get('recordings')[0].get('length')
        return song_duration/1000
    except Exception as ex:
        logger.error(ex)

if __name__ == "__main__":
    service = ShazamService()
    service.identify_song("test.wav")