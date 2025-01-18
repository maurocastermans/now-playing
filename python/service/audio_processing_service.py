import io
import logging
import numpy as np
from scipy.signal import resample
import scipy.io.wavfile as wav

logger = logging.getLogger(__name__)


class AudioProcessingService:
    def resample(self, audio: np.ndarray, source_sampling_rate: int, target_sampling_rate: int) -> np.ndarray:
        try:
            logger.info(f"Resampling audio from {source_sampling_rate} Hz to {target_sampling_rate} Hz.")
            samples = int(len(audio) * target_sampling_rate / source_sampling_rate)
            return np.squeeze(resample(audio, samples))
        except Exception as e:
            logger.error(f"Resampling failed: {e}")
            raise RuntimeError("Resampling failed.") from e

    def to_wav(self, audio: np.ndarray, sampling_rate: int) -> io.BytesIO:
        try:
            logger.info(f"Converting audio to WAV format at {sampling_rate} Hz.")
            buffer = io.BytesIO()
            wav.write(buffer, sampling_rate, audio)
            buffer.seek(0)
            return buffer
        except Exception as e:
            logger.error(f"WAV conversion failed: {e}")
            raise RuntimeError("WAV conversion failed.") from e
