import datetime
import logging
from typing import Dict, Optional, Any, Final
import requests
from dataclasses import dataclass

import sys
sys.path.append("..")
from logger import Logger
from util import Util
from config import Config


@dataclass(frozen=True)
class WeatherInfo:
    temperature: Optional[str]
    sub_description: Optional[str]
    fetched_at: Optional[datetime.datetime]


class WeatherService:
    def __init__(self) -> None:
        self._logger: logging.Logger = Logger().get_logger()
        self._config: dict = Config().get_config()

    def _build_request_url(self) -> str:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        api_key = self._config['weather']['openweathermap_api_key']
        self._latitude, self._longitude = Util.parse_coordinates(self._config['weather']['geo_coordinates'])
        return f"{base_url}?lat={self._latitude}&lon={self._longitude}&units=metric&appid={api_key}"

    def _fetch_weather_data(self) -> Optional[Dict[str, Any]]:
        try:
            url = self._build_request_url()
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self._logger.error(f"Error fetching weather data: {e}")
            return None

    def _extract_weather_info(self, data: Dict[str, Any]) -> WeatherInfo:
        try:
            temperature = f"{round(data['main']['temp'])}°C"
            feels_like_temperature = f"{round(data['main']['feels_like'])}°C"
            description = data['weather'][0]['description'].title()
            sub_description = f"Feels like {feels_like_temperature}. {description}."
            return WeatherInfo(
                temperature=temperature,
                sub_description=sub_description,
                fetched_at=datetime.datetime.now()
            )
        except KeyError as e:
            self._logger.error(f"Error processing weather data: missing key {e}")
            return WeatherService._default_weather_info()

    def get_weather_info(self) -> WeatherInfo:
        raw_data = self._fetch_weather_data()
        if not raw_data:
            return WeatherService._default_weather_info()
        return self._extract_weather_info(raw_data)

    @staticmethod
    def _default_weather_info() -> WeatherInfo:
        return WeatherInfo(
            temperature="inf",
            sub_description="No weather info",
            fetched_at=datetime.datetime.now()
        )
