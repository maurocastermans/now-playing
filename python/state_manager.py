import datetime
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field

from logger import Logger


class DisplayState(Enum):
    CLEAN = 0
    PLAYING = 1
    SCREENSAVER = 2
    UNKNOWN = 5


@dataclass
class PlayingState:
    song_remaining_duration: Optional[int] = None
    song_title: Optional[str] = None
    song_identified_time: Optional[datetime.datetime] = None


@dataclass
class ScreensaverState:
    weather_info: Optional[dict] = None


@dataclass
class AppState:
    current: DisplayState = DisplayState.UNKNOWN
    last_state_change: Optional[datetime.datetime] = field(default_factory=datetime.datetime.now)
    playing: PlayingState = field(default_factory=PlayingState)
    screensaver: ScreensaverState = field(default_factory=ScreensaverState)


class StateManager:
    def __init__(self):
        self.logger = Logger().get_logger()
        self.state = AppState()

    def set_state(self, new_state: DisplayState):
        if self.state.current != new_state:
            self.logger.info(f"State changed from {self.state.current.name} to {new_state.name}")
            self.state.current = new_state
            self.state.last_state_change = datetime.datetime.now()

    def set_playing_state(self, song_title: str, song_remaining_duration: int):
        self.state.playing.song_title = song_title
        self.state.playing.song_remaining_duration = song_remaining_duration
        self.state.playing.song_identified_time = datetime.datetime.now()
        self.set_state(DisplayState.PLAYING)

    def set_screensaver_state(self):
        self.set_state(DisplayState.PLAYING)

    def set_weather_state(self, weather_info: dict):
        self.state.screensaver.weather_info = weather_info

    def should_refresh_weather(self) -> bool:
        last_fetched = self.state.screensaver.weather_info["fetched_at"]
        return datetime.datetime.now() - last_fetched >= datetime.timedelta(minutes=30)

    def music_still_playing_but_song_ended(self) -> bool:
        return self.get_state() == DisplayState.PLAYING and datetime.datetime.now() - self.state.playing.song_identified_time >= datetime.timedelta(
            seconds=self.state.playing.song_remaining_duration)

    def no_song_identify_triggered_for_1_minute(self) -> bool:
        return self.state.current != DisplayState.SCREENSAVER and datetime.datetime.now() - self.state.last_state_change >= datetime.timedelta(
            minutes=1)

    def get_state(self):
        return self.state

    def get_playing_state(self):
        return self.state.playing

    def get_screensaver_state(self):
        return self.state.screensaver
