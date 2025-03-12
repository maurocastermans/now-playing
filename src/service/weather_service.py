import datetime
from typing import Dict, Optional, Any, Final
import requests
from dataclasses import dataclass

import sys

sys.path.append("..")
from logger import Logger
from util import Util


@dataclass(frozen=True)
class WeatherInfo:
    temperature: Optional[str]
    weather_sub_description: Optional[str]
    fetched_at: Optional[datetime.datetime]


class WeatherService:
    TEMPERATURE_UNIT: Final[str] = '°C'

    def __init__(self, api_key: str, geo_coordinates: str) -> None:
        self._logger = Logger().get_logger()
        self._api_key = api_key
        self._latitude, self._longitude = Util.parse_coordinates(geo_coordinates)

    def _build_request_url(self) -> str:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        return f"{base_url}?lat={self._latitude}&lon={self._longitude}&units=metric&appid={self._api_key}"

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
            temperature = f"{round(data['main']['temp'])}{WeatherService.TEMPERATURE_UNIT}"
            feels_like_temperature = f"{round(data['main']['feels_like'])}{WeatherService.TEMPERATURE_UNIT}"
            description = data['weather'][0]['description'].title()
            weather_sub_description = f"Feels like {feels_like_temperature}. {description}."
            return WeatherInfo(
                temperature=temperature,
                weather_sub_description=weather_sub_description,
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
            weather_sub_description="No weather info",
            fetched_at=datetime.datetime.now()
        )
