import logging
import sys
import numpy as np
import traceback
import signal
from typing import Tuple, Final

from logger import Logger
from src.config import Config
from state_manager import StateManager, DisplayState

from service.song_identify_service import SongIdentifyService, SongInfo
from audio_processing_utils import AudioProcessingUtils
from service.audio_recording_service import AudioRecordingService
from service.music_detection_service import MusicDetectionService
from service.weather_service import WeatherService, WeatherInfo
from service.display_service import DisplayService


class NowPlaying:
    # Constants
    AUDIO_DEVICE_SAMPLING_RATE: Final[int] = 44100
    AUDIO_DEVICE_NUMBER_OF_CHANNELS: Final[int] = 1
    AUDIO_RECORDING_DURATION_IN_SECONDS: Final[int] = 10
    SUPPORTED_SAMPLING_RATE_BY_MUSIC_DETECTION_AND_SONG_IDENTIFY: Final[int] = 16000

    def __init__(self):
        signal.signal(signal.SIGTERM, self._handle_exit)  # System or process termination
        signal.signal(signal.SIGINT, self._handle_exit)  # Ctrl+C termination

        # Singletons
        self._config: dict = Config().get_config()
        self._logger: logging.Logger = Logger().get_logger()
        self._state_manager: StateManager = StateManager()

        # Services
        self._audio_recording_service: AudioRecordingService = AudioRecordingService(
            sampling_rate=NowPlaying.AUDIO_DEVICE_SAMPLING_RATE,
            channels=NowPlaying.AUDIO_DEVICE_NUMBER_OF_CHANNELS
        )
        self._music_detection_service: MusicDetectionService = MusicDetectionService(
            audio_duration_in_seconds=NowPlaying.AUDIO_RECORDING_DURATION_IN_SECONDS
        )
        self._song_identify_service: SongIdentifyService = SongIdentifyService()
        self._weather_service: WeatherService = WeatherService()
        self._display_service: DisplayService = DisplayService()

    def run(self) -> None:
        while True:
            try:
                audio, is_music_detected = self._record_audio_and_detect_music()
                if is_music_detected:
                    self._handle_music_detected(audio)
                else:
                    self._handle_no_music_detected()
            except Exception as e:
                self._logger.error(f"Error occurred: {e}")
                self._logger.error(traceback.format_exc())

    def _record_audio_and_detect_music(self) -> Tuple[np.ndarray, bool]:
        recorded_audio = self._audio_recording_service.record(
            duration=NowPlaying.AUDIO_RECORDING_DURATION_IN_SECONDS
        )
        audio = AudioProcessingUtils.resample(
            recorded_audio,
            source_sampling_rate=NowPlaying.AUDIO_DEVICE_SAMPLING_RATE,
            target_sampling_rate=NowPlaying.SUPPORTED_SAMPLING_RATE_BY_MUSIC_DETECTION_AND_SONG_IDENTIFY
        )
        is_music_detected = self._music_detection_service.is_music_detected(audio)
        return audio, is_music_detected

    def _handle_music_detected(self, audio: np.ndarray) -> None:
        song_info = self._trigger_song_identify(audio)
        if (
                song_info
                and (self._state_manager.get_state().current != DisplayState.PLAYING
                     or self._state_manager.music_still_playing_but_different_song_identified(song_info.title))
        ):
            self._set_playing_state_and_update_display(song_info)

        self._state_manager.set_last_music_detected_time()

    def _trigger_song_identify(self, audio: np.ndarray) -> SongInfo:
        wav_audio = AudioProcessingUtils.to_wav(
            audio,
            sampling_rate=NowPlaying.SUPPORTED_SAMPLING_RATE_BY_MUSIC_DETECTION_AND_SONG_IDENTIFY
        )
        return self._song_identify_service.identify(wav_audio)

    def _set_playing_state_and_update_display(self, song_info: SongInfo) -> None:
        self._state_manager.set_playing_state(song_title=song_info.title)
        self._display_service.display_update_process(song_info=song_info)

    def _handle_no_music_detected(self) -> None:
        if (
                self._state_manager.get_state().current != DisplayState.SCREENSAVER and self._state_manager.no_music_detected_for_more_than_a_minute()
                or self._state_manager.screensaver_still_up_but_weather_info_outdated()
        ):
            weather_info = self._weather_service.get_weather_info()
            self._set_screensaver_state_and_update_display(weather_info)

    def _set_screensaver_state_and_update_display(self, weather_info: WeatherInfo) -> None:
        self._state_manager.set_screensaver_state(weather_info=weather_info)
        self._display_service.display_update_process(weather_info=weather_info)

    def _handle_exit(self, _sig, _frame):
        self._logger.warning(f"Stopping gracefully.")
        sys.exit(0)


if __name__ == "__main__":
    service = NowPlaying()
    service.run()
