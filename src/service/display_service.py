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
from logger import Logger
from config import Config


class DisplayService:
    def __init__(self) -> None:
        self._config: dict = Config().get_config()
        self._logger: logging.Logger = Logger().get_logger()
        self._inky = auto()

    def clean_display(self) -> None:
        try:
            for _ in range(2):
                for y in range(self._inky.height - 1):
                    for x in range(self._inky.width - 1):
                        self._inky.set_pixel(x, y, CLEAN)
                self._inky.show()
                time.sleep(1.0)
        except Exception as e:
            self._logger.error(f"Error cleaning display: {e}")
            self._logger.error(traceback.format_exc())

    def update_display_to_playing(self, song_info: SongInfo) -> None:
        album_cover_image = Image.open(requests.get(song_info.album_art, stream=True).raw)
        display_image = self._generate_display_image(album_cover_image, song_info.title, song_info.artist)
        self._show_image_on_display(display_image)

    def update_display_to_screensaver(self, weather_info: WeatherInfo) -> None:
        screensaver_image = Image.open(self._config['display']['screensaver_image'])
        display_image = self._generate_display_image(screensaver_image, weather_info.temperature,
                                                     weather_info.sub_description)
        self._show_image_on_display(display_image)

    def _generate_display_image(self, image: Image, title: str, subtitle: str) -> Image:
        image = self._fit_background_image(image)

        if self._config['display']['small_album_cover']:
            self._add_smaller_album_cover(image)

        self._add_text(image, title, subtitle)
        return image

    def _fit_background_image(self, image: Image) -> Image:
        display_width = self._config['display']['width']
        display_height = self._config['display']['height']
        return ImageOps.fit(image, (display_width, display_height), centering=(0, 0))

    def _add_smaller_album_cover(self, image) -> None:
        offset_px_top = self._config['display']['offset_top_px']
        small_album_cover_px = self._config['display']['small_album_cover_px']
        display_width = self._config['display']['width']
        small_album_cover_image = image.resize((small_album_cover_px, small_album_cover_px), Image.LANCZOS)
        image.paste(small_album_cover_image, ((display_width - small_album_cover_px) // 2, offset_px_top))

    def _add_text(self, image: Image, title: str, subtitle: str) -> None:
        subtitle_font = ImageFont.truetype(self._config['display']['font_path'],
                                           self._config['display']['font_size_subtitle'])
        subtitle_position_y = self._config['display']['height'] - (
                self._config['display']['offset_bottom_px'] + self._config['display']['font_size_subtitle'])
        subtitle_height = self._draw_text(image, subtitle, 'white', 'black', subtitle_font,
                                          subtitle_position_y)

        title_font = ImageFont.truetype(self._config['display']['font_path'],
                                        self._config['display']['font_size_title'])
        title_position_y = self._config['display']['height'] - (
                self._config['display']['offset_bottom_px'] + self._config['display'][
            'font_size_title']) - subtitle_height
        self._draw_text(image, title, 'white', 'black', title_font, title_position_y)

    def _draw_text(self, image: Image, text: str, text_color: str, shadow_text_color: str, font: ImageFont,
                   draw_position_y: int) -> int:
        offset_left_px = self._config['display']['offset_left_px']
        offset_right_px = self._config['display']['offset_right_px']
        offset_text_shadow_px = self._config['display']['offset_text_shadow_px']
        available_width = image.width - offset_left_px - offset_right_px - offset_text_shadow_px
        lines = DisplayService._break_text_to_lines(text, available_width, font)

        draw = ImageDraw.Draw(image)
        font_size = font.size
        if len(lines) > 1:
            draw_position_y -= (len(lines) - 1) * font_size

        for line in lines:
            if offset_text_shadow_px > 0:
                draw.text((offset_left_px + offset_text_shadow_px, draw_position_y + offset_text_shadow_px), line,
                          font=font,
                          fill=shadow_text_color)  # Draw shadow

            draw.text((offset_left_px, draw_position_y), line, font=font, fill=text_color)  # Draw the actual text

            draw_position_y += font_size

        return len(lines) * font.size

    def _show_image_on_display(self, image: Image, saturation: float = 0.5) -> None:
        try:
            self._inky.set_image(image, saturation=saturation)
            self._inky.show()
        except Exception as e:
            self._logger.error(f"Error displaying image: {e}")
            self._logger.error(traceback.format_exc())

    @staticmethod
    def _break_text_to_lines(text: str, max_width: int, font: ImageFont) -> list[str]:
        words = text.split()
        lines = []
        line = []

        def get_line_width(line_: list[str]) -> int:
            return int(ImageDraw.Draw(Image.new('RGB', (max_width, 1))).textlength(' '.join(line_), font=font))

        for word in words:
            line.append(word)
            line_width = get_line_width(line)

            if line_width > max_width:  # If the line is too wide, move the word to the next line
                lines.append(' '.join(line[:-1]))
                line = [word]  # Start a new line with the current word

        if line:  # Add the last line
            lines.append(' '.join(line))

        return lines
