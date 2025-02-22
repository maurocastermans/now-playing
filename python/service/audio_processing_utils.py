import io
import numpyå as np
from scipy.signal import resample
import scipy.io.wavfile as wav
from python.logger import Logger

class AudioProcessingUtils:
    logger = Logger().get_logger()

    @staticmethod
    def resample(audio: np.ndarray, source_sampling_rate: int, target_sampling_rate: int) -> np.ndarray:
        try:
            AudioProcessingUtils.logger.info(f"Resampling audio from {source_sampling_rate} Hz to {target_sampling_rate} Hz.")
            samples = int(len(audio) * target_sampling_rate / source_sampling_rate)
            return np.squeeze(resample(audio, samples))
        except Exception as e:
            AudioProcessingUtils.logger.error(f"Resampling failed: {e}")
            raise RuntimeError("Resampling failed.") from e

    @staticmethod
    def to_wav(audio: np.ndarray, sampling_rate: int) -> io.BytesIO:
        try:
            AudioProcessingUtils.logger.info(f"Converting audio to WAV format at {sampling_rate} Hz.")
            buffer = io.BytesIO()
            wav.write(buffer, sampling_rate, audio)
            buffer.seek(0)
            return buffer
        except Exception as e:
            AudioProcessingUtils.logger.error(f"WAV conversion failed: {e}")
            raise RuntimeError("WAV conversion failed.") from e
