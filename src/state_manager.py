import datetime
import logging
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from service.weather_service import WeatherInfo

from logger import Logger


class DisplayState(Enum):
    CLEAN = 0
    PLAYING = 1
    SCREENSAVER = 2
    UNKNOWN = 5


class StateData:
    pass


@dataclass(frozen=True)
class PlayingState(StateData):
    song_title: Optional[str] = None
    song_artist: Optional[str] = None


@dataclass(frozen=True)
class ScreensaverState(StateData):
    weather_info: Optional[WeatherInfo] = None


@dataclass(frozen=True)
class AppState:
    current: DisplayState = DisplayState.UNKNOWN
    data: Optional[StateData] = None


class StateManager:
    def __init__(self):
        self._logger: logging.Logger = Logger().get_logger()
        self._state: AppState = AppState()
        self._last_music_detected_time: Optional[datetime.datetime] = None
        self._image_counter: int = 0

    def _set_state(self, new_state: DisplayState, data: Optional[StateData]) -> None:
        old_state = self._state.current
        self._state = AppState(
            current=new_state,
            data=data
        )
        self._logger.info(f"State changed from {old_state.name} to {new_state.name}.")

    def set_clean_state(self) -> None:
        self._set_state(DisplayState.CLEAN, None)

    def set_playing_state(self, song_title: str, song_artist: str) -> None:
        playing_state = PlayingState(song_title=song_title, song_artist=song_artist)
        self._set_state(DisplayState.PLAYING, playing_state)

    def set_screensaver_state(self, weather_info: WeatherInfo) -> None:
        screensaver_state = ScreensaverState(weather_info=weather_info)
        self._set_state(DisplayState.SCREENSAVER, screensaver_state)

    def update_last_music_detected_time(self) -> None:
        self._last_music_detected_time = datetime.datetime.now()

    def increase_image_counter(self) -> None:
        self._image_counter += 1

    def should_clean_display(self) -> bool:
        if self._image_counter > 20:
            self._logger.debug("Display should be cleaned to avoid 'ghosting' from previous images.")
            self._image_counter = 0
            return True

    def no_music_detected_for_more_than_a_minute(self) -> bool:
        if self._last_music_detected_time is None:
            return True
        elapsed_time = datetime.datetime.now() - self._last_music_detected_time
        if elapsed_time >= datetime.timedelta(minutes=1):
            self._logger.info("No music detected for more than a minute.")
            return True
        return False

    def music_still_playing_but_different_song_identified(self, song_title: str):
        if self._state.current != DisplayState.PLAYING:
            return False
        if self.get_playing_state().song_title != song_title:
            self._logger.info("Music still playing but new song identified.")
            return True
        self._logger.debug("Same song still playing.")
        return False

    def screensaver_still_up_but_weather_info_outdated(self) -> bool:
        if self._state.current != DisplayState.SCREENSAVER:
            return False
        elapsed_time = datetime.datetime.now() - self._get_screensaver_state().weather_info.fetched_at
        if elapsed_time >= datetime.timedelta(minutes=60):
            self._logger.info("Weather info outdated.")
            return True

    def get_state(self) -> AppState:
        return self._state

    def get_playing_state(self) -> PlayingState:
        if self._state.current == DisplayState.PLAYING and isinstance(self._state.data, PlayingState):
            return self._state.data
        raise RuntimeError("Attempted to access PlayingState while not in PLAYING state.")

    def _get_screensaver_state(self) -> ScreensaverState:
        if self._state.current == DisplayState.SCREENSAVER and isinstance(self._state.data, ScreensaverState):
            return self._state.data
        raise RuntimeError("Attempted to access ScreensaverState while not in SCREENSAVER state.")
