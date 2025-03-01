import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field, replace

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
    song_remaining_duration: Optional[int] = None
    song_title: Optional[str] = None
    song_identified_time: Optional[datetime.datetime] = None


@dataclass(frozen=True)
class ScreensaverState(StateData):
    weather_info: Optional[dict] = None


@dataclass(frozen=True)
class AppState:
    current: DisplayState = DisplayState.UNKNOWN
    last_state_change_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    state_data: Optional[StateData] = None


class StateManager:
    def __init__(self) -> None:
        self.logger = Logger().get_logger()
        self.state = AppState()

    def set_state(self, new_state: DisplayState, state_data: Optional[StateData]) -> None:
        old_state = self.state.current
        if self.state.current != new_state:
            self.state = replace(
                self.state,
                current=new_state,
                last_state_change_time=datetime.datetime.now(),
                state_data=state_data
            )
            self.logger.info(f"State changed from {old_state.name} to {new_state.name}")

    def set_unknown_state(self) -> None:
        self.set_state(DisplayState.UNKNOWN, None)

    def set_clean_state(self) -> None:
        self.set_state(DisplayState.CLEAN, None)

    def set_playing_state(self, song_title: str, song_remaining_duration: int) -> None:
        playing_state = PlayingState(
            song_title=song_title,
            song_remaining_duration=song_remaining_duration,
            song_identified_time=datetime.datetime.now()
        )
        self.set_state(DisplayState.PLAYING, playing_state)

    def set_screensaver_state(self, weather_info: dict) -> None:
        screensaver_state = ScreensaverState(weather_info=weather_info)
        self.set_state(DisplayState.SCREENSAVER, screensaver_state)

    def weather_info_outdated(self) -> bool:
        if isinstance(self.state.state_data, ScreensaverState):
            last_fetched = self.state.state_data.weather_info["fetched_at"]
            return datetime.datetime.now() - last_fetched >= datetime.timedelta(minutes=1)
        return False

    def music_still_playing_but_song_ended(self) -> bool:
        if isinstance(self.state.state_data, PlayingState):
            elapsed_time = datetime.datetime.now() - self.state.state_data.song_identified_time
            return elapsed_time >= datetime.timedelta(seconds=self.state.state_data.song_remaining_duration)
        return False

    def no_song_identify_triggered_for_more_than_a_minute(self) -> bool:
        elapsed_time = datetime.datetime.now() - self.state.last_state_change_time
        return elapsed_time >= datetime.timedelta(minutes=1)

    def get_state(self) -> AppState:
        return self.state

    def get_playing_state(self) -> Optional[PlayingState]:
        if isinstance(self.state.state_data, PlayingState):
            return self.state.state_data
        return None

    def get_screensaver_state(self) -> Optional[ScreensaverState]:
        if isinstance(self.state.state_data, ScreensaverState):
            return self.state.state_data
        return None
