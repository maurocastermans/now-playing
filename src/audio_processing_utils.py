import io
import logging

import numpy as np
from scipy.signal import resample
import scipy.io.wavfile as wav
from logger import Logger

class AudioProcessingUtils:
    _logger: logging.Logger = Logger().get_logger()

    @staticmethod
    def resample(audio: np.ndarray, source_sampling_rate: int, target_sampling_rate: int) -> np.ndarray:
        try:
            samples = int(len(audio) * target_sampling_rate / source_sampling_rate)
            return np.squeeze(resample(audio, samples))
        except Exception as e:
            AudioProcessingUtils._logger.error(f"Resampling failed: {e}")
            raise RuntimeError("Resampling failed.") from e

    @staticmethod
    def to_wav(audio: np.ndarray, sampling_rate: int) -> io.BytesIO:
        try:
            buffer = io.BytesIO()
            wav.write(buffer, sampling_rate, audio)
            buffer.seek(0)
            return buffer
        except Exception as e:
            AudioProcessingUtils._logger.error(f"WAV conversion failed: {e}")
            raise RuntimeError("WAV conversion failed.") from e

    @staticmethod
    def float32_to_int16(audio: np.ndarray) -> np.ndarray:
        try:
            audio = np.clip(audio, -1.0, 1.0)  # Avoid overflow
            return np.int16(audio * 32767)
        except Exception as e:
            AudioProcessingUtils._logger.error(f"Conversion to int16 failed: {e}")
            raise RuntimeError("float32 to int16 conversion failed.") from e