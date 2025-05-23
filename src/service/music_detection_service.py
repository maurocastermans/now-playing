import csv
import logging

import numpy as np
from tflite_runtime.interpreter import Interpreter
from typing import List, Tuple, Final

import sys

sys.path.append("..")
from logger import Logger


class MusicDetectionService:
    SAMPLING_RATE: Final[int] = 16000
    CLASS_MAP_PATH: Final[str] = 'src/ml-model/yamnet_class_map.csv'
    MODEL_PATH: Final[str] = 'src/ml-model/1.tflite'
    CONFIDENCE_THRESHOLD: Final[float] = 0.2

    def __init__(self, audio_duration_in_seconds: int) -> None:
        self._logger: logging.Logger = Logger().get_logger()
        self._audio_duration_in_seconds: int = audio_duration_in_seconds

        self._interpreter: Interpreter = Interpreter(MusicDetectionService.MODEL_PATH)
        self._configure_interpreter()

        self._class_names: List[str] = self._load_class_names()

    def _configure_interpreter(self) -> None:
        self.input_details = self._interpreter.get_input_details()
        self.output_details = self._interpreter.get_output_details()

        self.waveform_input_index = self.input_details[0]['index']
        self.scores_output_index = self.output_details[0]['index']

        # Resize input tensor to match the expected duration
        input_shape = [self._audio_duration_in_seconds * MusicDetectionService.SAMPLING_RATE]
        self._interpreter.resize_tensor_input(self.waveform_input_index, input_shape, strict=True)

        self._interpreter.allocate_tensors()

    def _load_class_names(self) -> List[str]:
        try:
            with open(MusicDetectionService.CLASS_MAP_PATH, 'r') as csv_file:
                class_map_csv = csv.reader(csv_file)
                next(class_map_csv)  # Skip header row
                return [row[2] for row in class_map_csv]  # Only display_name column
        except FileNotFoundError:
            self._logger.error(f"Class map file not found at {MusicDetectionService.CLASS_MAP_PATH}")
            return []

    def _get_top_class(self, scores: np.ndarray) -> Tuple[str, float]:
        mean_scores = scores.mean(axis=0)
        top_index = mean_scores.argmax()
        return self._class_names[top_index], mean_scores[top_index]

    def is_music_detected(self, waveform: np.ndarray) -> bool:
        if not self._class_names:
            self._logger.error("Class names are not loaded. Cannot perform detection.")
            return False

        self._interpreter.set_tensor(self.waveform_input_index, waveform)
        self._interpreter.invoke()

        scores = self._interpreter.get_tensor(self.scores_output_index)

        top_class, confidence = self._get_top_class(scores)

        if top_class == 'Music' and confidence > MusicDetectionService.CONFIDENCE_THRESHOLD:
            self._logger.info(f"Music detected with confidence: {confidence:.2f}")
            return True

        self._logger.debug("No music detected.")
        return False
