import sys
import numpy as np
import os
import traceback
import signal
import yaml
from typing import Tuple

from logger import Logger
from state_manager import StateManager, DisplayState

from service.song_identify_service import SongIdentifyService, SongInfo
from audio_processing_utils import AudioProcessingUtils
from service.audio_recording_service import AudioRecordingService
from service.music_detection_service import MusicDetectionService
from service.weather_service import WeatherService, WeatherInfo
from service.display_service import DisplayService


class NowPlaying:
    def __init__(self):
        self._logger = Logger().get_logger()
        signal.signal(signal.SIGTERM, self._handle_exit)  # System or process termination
        signal.signal(signal.SIGINT, self._handle_exit)  # Ctrl+C termination

        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
        with open(config_path, 'r') as config_file:
            self._config = yaml.safe_load(config_file)

        openweathermap_api_key = self._config['weather']['openweathermap_api_key']
        geo_coordinates = self._config['weather']['geo_coordinates']

        self._audio_recording_service = AudioRecordingService(44100, 1, "USB")
        self._music_detection_service = MusicDetectionService(10)
        self._song_identify_service = SongIdentifyService()
        self._weather_service = WeatherService(openweathermap_api_key, geo_coordinates)

        self._state_manager = StateManager()
        self._display_service = DisplayService(self._config, self._state_manager)

    def _handle_exit(self, _sig, _frame):
        self._logger.warning(f"Stopping gracefully.")
        sys.exit(0)

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
        recorded_audio = self._audio_recording_service.record(10)
        audio = AudioProcessingUtils.resample(recorded_audio, 44100, 16000)
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
        wav_audio = AudioProcessingUtils.to_wav(audio, 16000)
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


if __name__ == "__main__":
    service = NowPlaying()
    service.run()
