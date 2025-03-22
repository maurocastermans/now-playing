import logging
import time
import traceback
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from service.weather_service import WeatherInfo
from service.song_identify_service import SongInfo
from inky.auto import auto
from inky.inky_uc8159 import CLEAN

import sys

sys.path.append("..")
from state_manager import StateManager
from logger import Logger
from config import Config


class DisplayService:
    def __init__(self) -> None:
        self._config: dict = Config().get_config()
        self._state_manager: StateManager = StateManager()
        self._logger: logging.Logger = Logger().get_logger()
        self._pic_counter: int = 0
        self._inky_display = auto()
        self._clean_display_and_set_clean_state()

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

    def _clean_display_and_set_clean_state(self) -> None:
        try:
            inky = self._inky_display()
            for _ in range(2):
                for y in range(inky.height - 1):
                    for x in range(inky.width - 1):
                        inky.set_pixel(x, y, CLEAN)
                inky.show()
                time.sleep(1.0)
            self._state_manager.set_clean_state()
        except Exception as e:
            self._logger.error(f'Error cleaning display: {e}')
            self._logger.error(traceback.format_exc())

    def _display_image(self, image: Image, saturation: float = 0.5):
        """displays a image on the inky display

        Args:
            image (Image): Image to display
            saturation (float, optional): saturation. Defaults to 0.5.
        """
        try:
            inky = self._inky_display()
            inky.set_image(image, saturation=saturation)
            inky.show()
        except Exception as e:
            self._logger.error(f'Display image error: {e}')
            self._logger.error(traceback.format_exc())

    def _gen_pic(self, image: Image, artist: str, title: str) -> Image:
        album_cover_small_px = self._config['display']['album_cover_small_px']
        offset_px_left = self._config['display']['offset_px_left']
        offset_px_right = self._config['display']['offset_px_right']
        offset_px_top = self._config['display']['offset_px_top']
        offset_px_bottom = self._config['display']['offset_px_bottom']
        offset_text_px_shadow = self._config['display']['offset_text_px_shadow']
        text_direction = self._config['display']['text_direction']
        # The width and height of the background
        bg_w, bg_h = image.size
        if self._config['display']['background_mode'] == 'fit':
            if bg_w < self._config['display']['width'] or bg_w > self._config['display']['width']:
                image_new = ImageOps.fit(image=image, size=(
                    self._config['display']['width'], self._config['display']['height']), centering=(0, 0))
            else:
                # no need to expand just crop
                image_new = image.crop(
                    (0, 0, self._config['display']['width'], self._config['display']['height']))
        if self._config['display']['background_mode'] == 'repeat':
            if bg_w < self._config['display']['width'] or bg_h < self._config['display']['height']:
                # we need to repeat the background
                # Creates a new empty image, RGB mode, and size of the display
                image_new = Image.new('RGB',
                                      (self._config['display']['width'], self._config['display']['height']))
                # Iterate through a grid, to place the background tile
                for x in range(0, self._config['display']['width'], bg_w):
                    for y in range(0, self._config['display']['height'], bg_h):
                        # paste the image at location x, y:
                        image_new.paste(image, (x, y))
            else:
                # no need to repeat just crop
                image_new = image.crop(
                    (0, 0, self._config['display']['width'], self._config['display']['height']))
        if self._config['display']['album_cover_small']:
            cover_smaller = image.resize([album_cover_small_px, album_cover_small_px], Image.LANCZOS)
            album_pos_x = (self._config['display']['width'] - album_cover_small_px) // 2
            image_new.paste(cover_smaller, [album_pos_x, offset_px_top])
        font_title = ImageFont.truetype(self._config['display']['font_path'],
                                        self._config['display']['font_size_title'])
        font_artist = ImageFont.truetype(self._config['display']['font_path'],
                                         self._config['display']['font_size_artist'])
        if text_direction == 'top-down':
            title_position_y = album_cover_small_px + offset_px_top + 10
            title_height = self._fit_text_top_down(img=image_new, text=title, text_color='white',
                                                   shadow_text_color='black', font=font_title,
                                                   font_size=self._config['display']['font_size_title'],
                                                   y_offset=title_position_y, x_start_offset=offset_px_left,
                                                   x_end_offset=offset_px_right,
                                                   offset_text_px_shadow=offset_text_px_shadow)
            artist_position_y = album_cover_small_px + offset_px_top + 10 + title_height
            self._fit_text_top_down(img=image_new, text=artist, text_color='white', shadow_text_color='black',
                                    font=font_artist, font_size=self._config['display']['font_size_artist'],
                                    y_offset=artist_position_y, x_start_offset=offset_px_left,
                                    x_end_offset=offset_px_right, offset_text_px_shadow=offset_text_px_shadow)
        if text_direction == 'bottom-up':
            artist_position_y = self._config['display']['height'] - (
                    offset_px_bottom + self._config['display']['font_size_artist'])
            artist_height = self._fit_text_bottom_up(img=image_new, text=artist, text_color='white',
                                                     shadow_text_color='black', font=font_artist,
                                                     font_size=self._config['display']['font_size_artist'],
                                                     y_offset=artist_position_y, x_start_offset=offset_px_left,
                                                     x_end_offset=offset_px_right,
                                                     offset_text_px_shadow=offset_text_px_shadow)
            title_position_y = self._config['display']['height'] - (
                    offset_px_bottom + self._config['display']['font_size_title']) - artist_height
            self._fit_text_bottom_up(img=image_new, text=title, text_color='white', shadow_text_color='black',
                                     font=font_title, font_size=self._config['display']['font_size_title'],
                                     y_offset=title_position_y, x_start_offset=offset_px_left,
                                     x_end_offset=offset_px_right, offset_text_px_shadow=offset_text_px_shadow)
        return image_new

    def display_update_process(self, song_info: SongInfo = None, weather_info: WeatherInfo = None):
        if song_info:
            image = self._gen_pic(Image.open(requests.get(song_info.album_art, stream=True).raw), song_info.artist,
                                  song_info.title)
        elif weather_info:

            # not song playing use logo + weather info
            image = self._gen_pic(Image.open(self._config['display']['no_song_cover']),
                                  weather_info.weather_sub_description,
                                  weather_info.temperature)
        else:
            # not song playing use logo
            image = self._gen_pic(Image.open(self._config['display']['no_song_cover']), 'shazampi-eink',
                                  'No song playing')
        # clean screen every x pics
        if self._pic_counter > self._config['display']['display_refresh_counter']:
            self._clean_display_and_set_clean_state()
            self._pic_counter = 0
        # display picture on display
        self._display_image(image)
        self._pic_counter += 1
