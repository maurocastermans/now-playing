import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass
from service.weather_service import WeatherInfo
from service.song_identify_service import SongInfo

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


@dataclass(frozen=True)
class ScreensaverState(StateData):
    weather_info: Optional[WeatherInfo] = None


@dataclass(frozen=True)
class AppState:
    current: DisplayState = DisplayState.UNKNOWN
    data: Optional[StateData] = None


class StateManager:
    def __init__(self) -> None:
        self.logger = Logger().get_logger()
        self.state = AppState()
        self.last_music_detected_time = None

    def set_state(self, new_state: DisplayState, data: Optional[StateData]) -> None:
        old_state = self.state.current
        self.state = AppState(
            current=new_state,
            data=data
        )
        self.logger.info(f"State change happened from {old_state.name} to {new_state.name}.")

    def set_clean_state(self) -> None:
        self.set_state(DisplayState.CLEAN, None)

    def set_playing_state(self, song_title: str) -> None:
        playing_state = PlayingState(song_title=song_title)
        self.set_state(DisplayState.PLAYING, playing_state)

    def set_screensaver_state(self, weather_info: WeatherInfo) -> None:
        screensaver_state = ScreensaverState(weather_info=weather_info)
        self.set_state(DisplayState.SCREENSAVER, screensaver_state)

    def set_last_music_detected_time(self) -> None:
        self.last_music_detected_time = datetime.datetime.now()

    def no_music_detected_for_more_than_one_minute(self) -> bool:
        if self.last_music_detected_time is None:
            return True
        elapsed_time = datetime.datetime.now() - self.last_music_detected_time
        if elapsed_time >= datetime.timedelta(minutes=1):
            self.logger.info("No music detected for more than 1 minute.")
            return True
        return False

    def music_still_playing_but_different_song_identified(self, song_info: SongInfo):
        return self.get_state().current == DisplayState.PLAYING and song_info.title != self.get_playing_state().song_title

    def screensaver_still_up_but_weather_info_outdated(self) -> bool:
        if self.state.current == DisplayState.SCREENSAVER and isinstance(self.state.data, ScreensaverState):
            last_fetched = self.state.data.weather_info.fetched_at
            if datetime.datetime.now() - last_fetched >= datetime.timedelta(minutes=60):
                self.logger.info("Weather info outdated.")
                return True
        return False

    def get_state(self) -> AppState:
        return self.state

    def get_playing_state(self) -> Optional[PlayingState]:
        if self.state.current == DisplayState.PLAYING and isinstance(self.state.data, PlayingState):
            return self.state.data
        return None

    def get_screensaver_state(self) -> Optional[ScreensaverState]:
        if self.state.current == DisplayState.SCREENSAVER and isinstance(self.state.data, ScreensaverState):
            return self.state.data
        return None
