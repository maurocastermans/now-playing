import logging
import time
import traceback
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps
from service.weather_service import WeatherInfo
from service.song_identify_service import SongInfo
from inky.auto import auto
from inky.inky_uc8159 import CLEAN
from typing import Any

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
        self._inky_display: Any = auto
        self._clean_display()
        self._state_manager.set_clean_state()

    def _clean_display(self) -> None:
        try:
            inky = self._inky_display()
            for _ in range(2):
                for y in range(inky.height - 1):
                    for x in range(inky.width - 1):
                        inky.set_pixel(x, y, CLEAN)
                inky.show()
                time.sleep(1.0)
        except Exception as e:
            self._logger.error(f'Error cleaning display: {e}')
            self._logger.error(traceback.format_exc())

    def _display_image(self, image: Image, saturation: float = 0.5):
        try:
            inky = self._inky_display()
            inky.set_image(image, saturation=saturation)
            inky.show()
        except Exception as e:
            self._logger.error(f'Error displaying image: {e}')
            self._logger.error(traceback.format_exc())

    def _generate_background_image(self, image: Image) -> Image:
        display_width, display_height = self._config['display']['width'], self._config['display']['height']
        image_width, image_height = image.size
        mode = self._config['display']['background_mode']

        if mode == "fit":
            return ImageOps.fit(image, (display_width, display_height), centering=(0, 0))
        elif mode == "repeat":
            new_image = Image.new("RGB", (display_width, display_height))
            # Loop through the display space in increments of the image size
            for x in range(0, display_width, image_width):
                for y in range(0, display_height, image_height):
                    new_image.paste(image, (x, y))
            return new_image

    def _generate_display_image(self, image: Image, artist: str, title: str) -> Image:
        image = self._generate_background_image(image)
        if self._config['display']['album_cover_small']:
            image = self._generate_smaller_album_cover(image)

        offset_px_left, offset_px_right = self._config['display']['offset_px_left'], self._config['display'][
            'offset_px_right']
        offset_px_bottom = self._config['display']['offset_px_bottom']
        offset_text_px_shadow = self._config['display']['offset_text_px_shadow']

        font_title = ImageFont.truetype(self._config['display']['font_path'],
                                        self._config['display']['font_size_title'])
        font_artist = ImageFont.truetype(self._config['display']['font_path'],
                                         self._config['display']['font_size_artist'])

        title_position_y = self._config['display']['height'] - (
                offset_px_bottom + self._config['display']['font_size_artist'])
        title_height = self._draw_text_bottom_up(image=image, text=artist, text_color='white',
                                                 shadow_text_color='black', font=font_artist,
                                                 font_size=self._config['display']['font_size_artist'],
                                                 y_offset=title_position_y, x_start_offset=offset_px_left,
                                                 x_end_offset=offset_px_right,
                                                 offset_text_px_shadow=offset_text_px_shadow)
        subtitle_position_y = self._config['display']['height'] - (
                offset_px_bottom + self._config['display']['font_size_title']) - title_height
        self._draw_text_bottom_up(image=image, text=title, text_color='white', shadow_text_color='black',
                                  font=font_title, font_size=self._config['display']['font_size_title'],
                                  y_offset=subtitle_position_y, x_start_offset=offset_px_left,
                                  x_end_offset=offset_px_right, offset_text_px_shadow=offset_text_px_shadow)
        return image

    def _generate_smaller_album_cover(self, image) -> Image:
        offset_px_top = self._config['display']['offset_px_top']
        album_cover_small_px = self._config['display']['album_cover_small_px']
        display_width = self._config['display']['width']
        cover_smaller = image.resize((album_cover_small_px, album_cover_small_px), Image.LANCZOS)
        x_pos = (display_width - album_cover_small_px) // 2
        image.paste(cover_smaller, (x_pos, offset_px_top))
        return image

    def update_display_to_playing(self, song_info: SongInfo):
        album_cover_image = Image.open(requests.get(song_info.album_art, stream=True).raw)
        display_image = self._generate_display_image(album_cover_image, song_info.artist, song_info.title)
        self._update_display(display_image)

    def update_display_to_screensaver(self, weather_info: WeatherInfo):
        screensaver_image = Image.open(self._config['display']['no_song_cover'])
        display_image = self._generate_display_image(screensaver_image, weather_info.weather_sub_description,
                                                     weather_info.temperature)
        self._update_display(display_image)

    def _update_display(self, display_image: Image):
        if self._pic_counter > self._config['display']['display_refresh_counter']:
            self._clean_display()
            self._state_manager.set_clean_state()
            self._pic_counter = 0
        self._display_image(display_image)
        self._pic_counter += 1

    def _draw_text_bottom_up(self, image: Image, text: str, text_color: str, shadow_text_color: str, font: ImageFont,
                             y_offset: int, font_size: int, x_start_offset: int = 0, x_end_offset: int = 0,
                             offset_text_px_shadow: int = 0) -> int:
        available_width = image.width - x_start_offset - x_end_offset - offset_text_px_shadow
        lines = DisplayService._break_text_to_lines(text, available_width, font)

        # Draw the text starting from the bottom upwards
        draw = ImageDraw.Draw(image)
        total_height = 0
        current_y = image.height - y_offset

        for line in reversed(lines):
            if offset_text_px_shadow > 0:
                # Draw shadow
                draw.text((x_start_offset + offset_text_px_shadow, current_y + offset_text_px_shadow), line, font=font, fill=shadow_text_color)

            # Draw the actual text
            draw.text((x_start_offset, current_y), line, font=font, fill=text_color)

            # Update the vertical position and height
            current_y -= font.size
            total_height += font.size

        return total_height

    @staticmethod
    def _break_text_to_lines(text: str, max_width: int, font: ImageFont) -> list[str]:
        words = text.split()  # Split text into words
        lines = []
        line = []

        # Helper function to calculate the width of a line when joined as a string
        def get_line_width(words_in_line: list[str]) -> int:
            return int(ImageDraw.Draw(Image.new('RGB', (max_width, 1))).textlength(' '.join(words_in_line), font=font))

        for word in words:
            line.append(word)
            line_width = get_line_width(line)

            # If the line is too wide, move the word to the next line
            if line_width > max_width:
                lines.append(' '.join(line[:-1]))
                line = [word]  # Start a new line with the current word

        # Add the last line
        if line:
            lines.append(' '.join(line))

        return lines
