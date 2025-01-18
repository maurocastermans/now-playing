import datetime
from typing import Dict, Optional, Any
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self, api_key: str, geo_coordinates: str) -> None:
        self.api_key = api_key
        self.latitude, self.longitude = self._parse_coordinates(geo_coordinates)
        self.temp_display_unit = '°C'

    # TODO extract
    @staticmethod
    def _parse_coordinates(geo_coordinates: str) -> tuple[float, float]:
        try:
            lat, lon = map(lambda x: float(x.strip()), geo_coordinates.split(','))
            return lat, lon
        except ValueError:
            logger.error("Invalid geo_coordinates format. Expected 'lat,lon' with numeric values.")
            raise ValueError("Invalid geo_coordinates format. Expected 'lat,lon' with numeric values.")

    def _build_request_url(self) -> str:
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        return f"{base_url}?lat={self.latitude}&lon={self.longitude}&units=metric&appid={self.api_key}"

    def fetch_weather_data(self) -> Optional[Dict]:
        try:
            url = self._build_request_url()
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return None

    def _extract_weather_info(self, data: Optional[Dict]) -> Dict[str, Optional[Any]]:
        if not data:
            return self._default_weather_response()

        try:
            temperature = f"{round(data['main']['temp'])}{self.temp_display_unit}"
            feels_like_temperature = f"{round(data['main']['feels_like'])}{self.temp_display_unit}"
            description = data['weather'][0]['description'].title()
            weather_sub_description = f"Feels like {feels_like_temperature}. {description}."
            return {
                "temperature": temperature,
                "weather_sub_description": weather_sub_description
            }
        except KeyError as e:
            logger.error(f"Error processing weather data: missing key {e}")
            return self._default_weather_response()

    def get_weather(self) -> Dict[str, Optional[Any]]:
        raw_data = self.fetch_weather_data()
        weather_info = self._extract_weather_info(raw_data)
        weather_info["fetched_at"] = datetime.datetime.now()
        return weather_info

    def _default_weather_response(self) -> Dict[str, Optional[str]]:
        return {
            "temperature": "inf",
            "weather_sub_description": "No weather info",
        }
