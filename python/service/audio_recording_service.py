import sounddevice as sd
import numpy as np
from typing import Optional, Tuple

import sys
sys.path.append("..")
from logger import Logger

class AudioRecordingService:
    def __init__(self, sampling_rate: int, channels: int, device_substring: str = 'USB') -> None:
        self._logger = Logger().get_logger()
        self._device_substring = device_substring
        self._sampling_rate = sampling_rate
        self._channels = channels
        self._setup_device()

    def _setup_device(self) -> None:
        try:
            sd.default.samplerate = self._sampling_rate
            sd.default.channels = self._channels
            device_information = self._get_device_information()
            if device_information:
                device_index, device_name = device_information
                sd.default.device = (device_index, None)
                self._logger.info(f"Using audio device: {device_name}")
            else:
                self._logger.warning(
                    f"No audio device found matching '{self._device_substring}'. Defaulting to system device.")
        except Exception as e:
            self._logger.error(f"Audio device setup failed: {e}")
            raise RuntimeError("Audio device setup failed.") from e

    def _get_device_information(self) -> Optional[Tuple[int, str]]:
        try:
            devices = sd.query_devices()
            for idx, device in enumerate(devices):
                if self._device_substring.lower() in device['name'].lower():
                    return idx, device['name']
            return None
        except Exception as e:
            self._logger.error(f"Device query failed: {e}")
            return None

    def record(self, duration: float) -> np.ndarray:
        if duration <= 0:
            raise ValueError("Duration must be positive.")

        try:
            self._logger.info(f"Recording for {duration} seconds at {self._sampling_rate} Hz.")
            audio = sd.rec(int(duration * self._sampling_rate), dtype=np.float32)
            sd.wait()
            self._logger.info("Recording finished.")
            return np.squeeze(audio)
        except Exception as e:
            self._logger.error(f"Recording failed: {e}")
            raise RuntimeError("Recording failed.") from e
