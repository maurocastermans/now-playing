import logging
import sounddevice as sd
import numpy as np
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class AudioRecordingService:
    def __init__(self, device_substring: str = 'USB', sampling_rate: int = 44100, channels: int = 1) -> None:
        logger.debug("Initializing AudioRecordingService...")
        self.device_substring = device_substring
        self.sampling_rate = sampling_rate
        self.channels = channels
        self._setup_device()

    def _setup_device(self) -> None:
        try:
            sd.default.samplerate = self.sampling_rate
            sd.default.channels = self.channels
            device_information = self._get_device_information()
            if device_information is not None:
                device_index, device_name = device_information
                sd.default.device = (device_index, None)
                logger.info(f"Using audio device: {device_name}")
            else:
                logger.warning(
                    f"No audio device found matching '{self.device_substring}'. Defaulting to system device.")
        except Exception as e:
            logger.error(f"Audio device setup failed: {e}")
            raise RuntimeError("Audio device setup failed.") from e

    def _get_device_information(self) -> Optional[Tuple[int, str]]:
        try:
            devices = sd.query_devices()
            for idx, device in enumerate(devices):
                if self.device_substring.lower() in device['name'].lower():
                    return idx, device['name']
            return None
        except Exception as e:
            logger.error(f"Device query failed: {e}")
            return None

    def record(self, duration: float) -> np.ndarray:
        if duration <= 0:
            raise ValueError("Duration must be positive.")

        try:
            logger.info(f"Recording for {duration} seconds at {self.sampling_rate} Hz.")
            audio = sd.rec(int(duration * self.sampling_rate), dtype=np.float32)
            sd.wait()
            logger.info("Recording finished.")
            return np.squeeze(audio)
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            raise RuntimeError("Recording failed.") from e
