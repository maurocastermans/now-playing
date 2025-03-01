from __future__ import annotations

import datetime
import time
import sys
from collections import namedtuple
from enum import Enum
from logger import Logger
import os
import traceback
import configparser

import requests
import signal
from dataclasses import dataclass, field
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance

from service.song_identify_service import SongIdentifyService
from service.audio_processing_utils import AudioProcessingUtils
from service.audio_recording_service import AudioRecordingService
from service.music_detection_service import MusicDetectionService
from service.weather_service import WeatherService

from inky.auto import auto
from inky.inky_uc8159 import CLEAN
from typing import Optional

SongInfo = namedtuple('SongInfo', ['title', 'artist', 'album_art', 'offset', 'song_duration'])


class DisplayState(Enum):
    CLEAN = 0
    PLAYING = 1
    SCREENSAVER = 2
    UNKNOWN = 5


@dataclass
class PlayingState:
    song_remaining_duration: int
    song_title: Optional[str]
    song_identified_time: datetime.datetime


@dataclass
class ScreensaverState:
    weather_info: dict


@dataclass
class AppState:
    current_state: DisplayState = DisplayState.UNKNOWN
    playing_state: Optional[PlayingState] = None
    screensaver_state: Optional[ScreensaverState] = None


class NowPlaying:
    def __init__(self, delay=120, recording_duration=10):
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.delay = delay
        self.recording_duration = recording_duration

        # Configuration for the matrix
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(os.path.dirname(__file__), '..', 'config', 'eink_options.ini'))

        self.logger = Logger().get_logger()

        openweathermap_api_key = self.config.get('DEFAULT', 'openweathermap_api_key')
        geo_coordinates = self.config.get('DEFAULT', 'geo_coordinates')

        self.audio_recording_service = AudioRecordingService(44100, 1, "USB")
        self.music_detection_service = MusicDetectionService(self.recording_duration)
        self.song_identify_service = SongIdentifyService()
        self.weather_service = WeatherService(openweathermap_api_key, geo_coordinates)

        self.pic_counter = 0
        self.state = AppState()
        self.inky_auto = auto
        self.inky_clean = CLEAN

    def _handle_sigterm(self, sig, frame):
        self.logger.warning('SIGTERM received stopping')
        sys.exit(0)

    def _break_fix(self, text: str, width: int, font: ImageFont, draw: ImageDraw):
        """
        Fix line breaks in text.
        """
        if not text:
            return
        if isinstance(text, str):
            text = text.split()  # this creates a list of words
        lo = 0
        hi = len(text)
        while lo < hi:
            mid = (lo + hi + 1) // 2
            t = ' '.join(text[:mid])  # this makes a string again
            w = int(draw.textlength(text=t, font=font))
            if w <= width:
                lo = mid
            else:
                hi = mid - 1
        t = ' '.join(text[:lo])  # this makes a string again
        w = int(draw.textlength(text=t, font=font))
        yield t, w
        yield from self._break_fix(text[lo:], width, font, draw)

    def _fit_text_top_down(self, img: Image, text: str, text_color: str, shadow_text_color: str, font: ImageFont,
                           y_offset: int, font_size: int, x_start_offset: int = 0, x_end_offset: int = 0,
                           offset_text_px_shadow: int = 0) -> int:
        """
        Fit text into container after applying line breaks. Returns the total
        height taken up by the text
        """
        width = img.width - x_start_offset - x_end_offset - offset_text_px_shadow
        draw = ImageDraw.Draw(img)
        pieces = list(self._break_fix(text, width, font, draw))
        y = y_offset
        h_taken_by_text = 0
        for t, _ in pieces:
            if offset_text_px_shadow > 0:
                draw.text((x_start_offset + offset_text_px_shadow, y + offset_text_px_shadow), t, font=font,
                          fill=shadow_text_color)
            draw.text((x_start_offset, y), t, font=font, fill=text_color)
            new_height = font_size
            y += font_size
            h_taken_by_text += new_height
        return h_taken_by_text

    def _fit_text_bottom_up(self, img: Image, text: str, text_color: str, shadow_text_color: str, font: ImageFont,
                            y_offset: int, font_size: int, x_start_offset: int = 0, x_end_offset: int = 0,
                            offset_text_px_shadow: int = 0) -> int:
        """
        Fit text into container after applying line breaks. Returns the total
        height taken up by the text
        """
        width = img.width - x_start_offset - x_end_offset - offset_text_px_shadow
        draw = ImageDraw.Draw(img)
        pieces = list(self._break_fix(text, width, font, draw))
        y = y_offset
        if len(pieces) > 1:
            y -= (len(pieces) - 1) * font_size
        h_taken_by_text = 0
        for t, _ in pieces:
            if offset_text_px_shadow > 0:
                draw.text((x_start_offset + offset_text_px_shadow, y + offset_text_px_shadow), t, font=font,
                          fill=shadow_text_color)
            draw.text((x_start_offset, y), t, font=font, fill=text_color)
            new_height = font_size
            y += font_size
            h_taken_by_text += new_height
        return h_taken_by_text

    def _display_clean(self):
        """cleans the display
        """
        try:
            inky = self.inky_auto()
            for _ in range(2):
                for y in range(inky.height - 1):
                    for x in range(inky.width - 1):
                        inky.set_pixel(x, y, self.inky_clean)

                inky.show()
                time.sleep(1.0)
            self.state.current_state = DisplayState.CLEAN
        except Exception as e:
            self.logger.error(f'Display clean error: {e}')
            self.logger.error(traceback.format_exc())

    def _display_image(self, image: Image, saturation: float = 0.5):
        """displays a image on the inky display

        Args:
            image (Image): Image to display
            saturation (float, optional): saturation. Defaults to 0.5.
        """
        try:
            inky = self.inky_auto()
            inky.set_image(image, saturation=saturation)
            inky.show()
        except Exception as e:
            self.logger.error(f'Display image error: {e}')
            self.logger.error(traceback.format_exc())

    def _gen_pic(self, image: Image, artist: str, title: str) -> Image:
        """Generates the Picture for the display

        Args:
            image (Image): album cover to be used
            artist (str): Artist text
            title (str): Song text

        Returns:
            Image: The finished image
        """
        album_cover_small_px = self.config.getint('DEFAULT', 'album_cover_small_px')
        offset_px_left = self.config.getint('DEFAULT', 'offset_px_left')
        offset_px_right = self.config.getint('DEFAULT', 'offset_px_right')
        offset_px_top = self.config.getint('DEFAULT', 'offset_px_top')
        offset_px_bottom = self.config.getint('DEFAULT', 'offset_px_bottom')
        offset_text_px_shadow = self.config.getint('DEFAULT', 'offset_text_px_shadow')
        text_direction = self.config.get('DEFAULT', 'text_direction')
        # The width and height of the background
        bg_w, bg_h = image.size
        if self.config.get('DEFAULT', 'background_mode') == 'fit':
            if bg_w < self.config.getint('DEFAULT', 'width') or bg_w > self.config.getint('DEFAULT', 'width'):
                image_new = ImageOps.fit(image=image, size=(
                    self.config.getint('DEFAULT', 'width'), self.config.getint('DEFAULT', 'height')), centering=(0, 0))
            else:
                # no need to expand just crop
                image_new = image.crop(
                    (0, 0, self.config.getint('DEFAULT', 'width'), self.config.getint('DEFAULT', 'height')))
        if self.config.get('DEFAULT', 'background_mode') == 'repeat':
            if bg_w < self.config.getint('DEFAULT', 'width') or bg_h < self.config.getint('DEFAULT', 'height'):
                # we need to repeat the background
                # Creates a new empty image, RGB mode, and size of the display
                image_new = Image.new('RGB',
                                      (self.config.getint('DEFAULT', 'width'), self.config.getint('DEFAULT', 'height')))
                # Iterate through a grid, to place the background tile
                for x in range(0, self.config.getint('DEFAULT', 'width'), bg_w):
                    for y in range(0, self.config.getint('DEFAULT', 'height'), bg_h):
                        # paste the image at location x, y:
                        image_new.paste(image, (x, y))
            else:
                # no need to repeat just crop
                image_new = image.crop(
                    (0, 0, self.config.getint('DEFAULT', 'width'), self.config.getint('DEFAULT', 'height')))
        if self.config.getboolean('DEFAULT', 'album_cover_small'):
            cover_smaller = image.resize([album_cover_small_px, album_cover_small_px], Image.LANCZOS)
            album_pos_x = (self.config.getint('DEFAULT', 'width') - album_cover_small_px) // 2
            image_new.paste(cover_smaller, [album_pos_x, offset_px_top])
        font_title = ImageFont.truetype(self.config.get('DEFAULT', 'font_path'),
                                        self.config.getint('DEFAULT', 'font_size_title'))
        font_artist = ImageFont.truetype(self.config.get('DEFAULT', 'font_path'),
                                         self.config.getint('DEFAULT', 'font_size_artist'))
        if text_direction == 'top-down':
            title_position_y = album_cover_small_px + offset_px_top + 10
            title_height = self._fit_text_top_down(img=image_new, text=title, text_color='white',
                                                   shadow_text_color='black', font=font_title,
                                                   font_size=self.config.getint('DEFAULT', 'font_size_title'),
                                                   y_offset=title_position_y, x_start_offset=offset_px_left,
                                                   x_end_offset=offset_px_right,
                                                   offset_text_px_shadow=offset_text_px_shadow)
            artist_position_y = album_cover_small_px + offset_px_top + 10 + title_height
            self._fit_text_top_down(img=image_new, text=artist, text_color='white', shadow_text_color='black',
                                    font=font_artist, font_size=self.config.getint('DEFAULT', 'font_size_artist'),
                                    y_offset=artist_position_y, x_start_offset=offset_px_left,
                                    x_end_offset=offset_px_right, offset_text_px_shadow=offset_text_px_shadow)
        if text_direction == 'bottom-up':
            artist_position_y = self.config.getint('DEFAULT', 'height') - (
                    offset_px_bottom + self.config.getint('DEFAULT', 'font_size_artist'))
            artist_height = self._fit_text_bottom_up(img=image_new, text=artist, text_color='white',
                                                     shadow_text_color='black', font=font_artist,
                                                     font_size=self.config.getint('DEFAULT', 'font_size_artist'),
                                                     y_offset=artist_position_y, x_start_offset=offset_px_left,
                                                     x_end_offset=offset_px_right,
                                                     offset_text_px_shadow=offset_text_px_shadow)
            title_position_y = self.config.getint('DEFAULT', 'height') - (
                    offset_px_bottom + self.config.getint('DEFAULT', 'font_size_title')) - artist_height
            self._fit_text_bottom_up(img=image_new, text=title, text_color='white', shadow_text_color='black',
                                     font=font_title, font_size=self.config.getint('DEFAULT', 'font_size_title'),
                                     y_offset=title_position_y, x_start_offset=offset_px_left,
                                     x_end_offset=offset_px_right, offset_text_px_shadow=offset_text_px_shadow)
        return image_new

    def _display_update_process(self, song_info: SongInfo = None, weather_info=None):
        """
        Args:
            song_info (SongInfo)
        Returns:
            int: updated picture refresh counter
        """
        if song_info:
            # download cover
            image = self._gen_pic(Image.open(requests.get(song_info.album_art, stream=True).raw), song_info.artist,
                                  song_info.title)
        elif weather_info:

            # not song playing use logo + weather info
            image = self._gen_pic(Image.open(self.config.get('DEFAULT', 'no_song_cover')),
                                  weather_info['weather_sub_description'],
                                  weather_info['temperature'])
        else:
            # not song playing use logo
            image = self._gen_pic(Image.open(self.config.get('DEFAULT', 'no_song_cover')), 'shazampi-eink',
                                  'No song playing')
        # clean screen every x pics
        if self.pic_counter > self.config.getint('DEFAULT', 'display_refresh_counter'):
            self._display_clean()
            self.pic_counter = 0
        # display picture on display
        self._display_image(image)
        self.pic_counter += 1

    def _trigger_song_identify(self, audio) -> SongInfo:
        """get the currently playing song

        Returns:
            SongInfo: with song name, album cover url, artist's name's
        """
        wav_audio = AudioProcessingUtils.to_wav(audio, 16000)
        song_info_dict = self.song_identify_service.identify(wav_audio)
        if song_info_dict:
            self.logger.debug("found song")
            return SongInfo(title=song_info_dict['title'],
                            artist=song_info_dict['artist'],
                            album_art=song_info_dict['album_art'],
                            song_duration=song_info_dict['song_duration'],
                            offset=song_info_dict['offset'])
        else:
            self.logger.debug("couldn't identify the music")

    def start(self) -> None:
        self._display_clean()
        self.state.playing_state = PlayingState(song_remaining_duration=self.delay, song_title=None,
                                                song_identified_time=datetime.datetime.now())
        self.state.screensaver_state = ScreensaverState(self.weather_service.get_weather_info())
        try:
            while True:
                try:
                    audio, is_music_playing = self._record_audio_and_detect_music()
                    if is_music_playing:
                        self._handle_music_playing(audio)
                    else:
                        self._handle_no_music_playing()
                except Exception as e:
                    self.logger.error(f'Error: {e}')
                    self.logger.error(traceback.format_exc())
        except KeyboardInterrupt:
            self.logger.info('Stopped application...')
            sys.exit(0)

    def _update_weather_info_if_outdated(self):
        if datetime.datetime.now() - self.state.screensaver_state.weather_info["fetched_at"] >= datetime.timedelta(
                minutes=30):
            self.state.screensaver_state.weather_info = self.weather_service.get_weather_info()

    def _record_audio_and_detect_music(self):
        audio = AudioProcessingUtils.resample(
            self.audio_recording_service.record(self.recording_duration),
            44100,
            16000
        )
        is_music_playing = self.music_detection_service.is_music_playing(audio)
        return audio, is_music_playing

    def _handle_music_playing(self, audio):
        if self.state.current_state != DisplayState.PLAYING or datetime.datetime.now() - self.state.playing_state.song_identified_time >= datetime.timedelta(
                seconds=self.state.playing_state.song_remaining_duration):
            song_info = self._trigger_song_identify(audio)
            self.state.playing_state.song_identified_time = datetime.datetime.now()
            self.state.playing_state.song_remaining_duration = self._calculate_remaining_song_duration(song_info)

            if song_info and song_info.title != self.state.playing_state.song_title:
                self._display_update_process(song_info=song_info)
                self.state.playing_state.song_title = song_info.title
            self.current_view = DisplayState.PLAYING

    def _calculate_remaining_song_duration(self, song_info):
        if song_info and song_info.song_duration and song_info.offset:
            return max(self.delay, song_info.song_duration - song_info.offset - self.recording_duration)
        return 30  # Default retry interval if song identification fails

    def _handle_no_music_playing(self):
        self._update_weather_info_if_outdated()
        if self.current_view != DisplayState.SCREENSAVER and datetime.datetime.now() - self.state.playing_state.song_identified_time >= datetime.timedelta(
                minutes=1):
            self._display_update_process(weather_info=self.state.screensaver_state.weather_info)
            self.current_view = DisplayState.SCREENSAVER


if __name__ == "__main__":
    service = NowPlaying()
    service.start()
