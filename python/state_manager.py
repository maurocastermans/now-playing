import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field, replace
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
    song_remaining_duration: Optional[float] = None


@dataclass(frozen=True)
class ScreensaverState(StateData):
    weather_info: Optional[WeatherInfo] = None


@dataclass(frozen=True)
class AppState:
    current: DisplayState = DisplayState.UNKNOWN
    last_state_change_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    data: Optional[StateData] = None


class StateManager:
    def __init__(self) -> None:
        self.logger = Logger().get_logger()
        self.state = AppState()

    def set_state(self, new_state: DisplayState, data: Optional[StateData]) -> None:
        old_state = self.state.current
        self.state = AppState(
            current=new_state,
            last_state_change_time=datetime.datetime.now(),
            data=data
        )
        self.logger.info(f"State change happened from {old_state.name} to {new_state.name}.")

    def set_clean_state(self) -> None:
        self.set_state(DisplayState.CLEAN, None)

    def set_playing_state(self, song_remaining_duration: float) -> None:
        playing_state = PlayingState(song_remaining_duration=song_remaining_duration)
        self.set_state(DisplayState.PLAYING, playing_state)

    def set_screensaver_state(self, weather_info: WeatherInfo) -> None:
        screensaver_state = ScreensaverState(weather_info=weather_info)
        self.set_state(DisplayState.SCREENSAVER, screensaver_state)

    def screensaver_still_up_but_weather_info_outdated(self) -> bool:
        if self.state.current == DisplayState.SCREENSAVER and isinstance(self.state.data, ScreensaverState):
            last_fetched = self.state.data.weather_info.fetched_at
            return datetime.datetime.now() - last_fetched >= datetime.timedelta(minutes=60)
        return False

    def music_is_still_playing_but_previous_song_ended(self) -> bool:
        if self.state.current == DisplayState.PLAYING and isinstance(self.state.data, PlayingState):
            elapsed_time = datetime.datetime.now() - self.state.last_state_change_time
            return elapsed_time >= datetime.timedelta(seconds=self.state.data.song_remaining_duration)
        return False

    def idle_for_more_than_one_minute(self) -> bool:
        elapsed_time = datetime.datetime.now() - self.state.last_state_change_time
        return elapsed_time >= datetime.timedelta(minutes=1)

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
