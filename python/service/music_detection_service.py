import csv
import numpy as np
from tflite_runtime.interpreter import Interpreter
from typing import List, Tuple

import sys
sys.path.append("..")
from logger import Logger


class MusicDetectionService:
    def __init__(self, recording_duration: int, model_path: str = 'python/ml-model/1.tflite',
                 class_map_path: str = 'python/ml-model/yamnet_class_map.csv') -> None:
        self._logger = Logger().get_logger()
        self._recording_duration = recording_duration
        self._sampling_rate = 16000
        self._model_path = model_path
        self._class_map_path = class_map_path

        self._interpreter = Interpreter('python/ml-model/1.tflite')
        self._configure_interpreter()

        self._class_names = self._load_class_names()

    def _configure_interpreter(self) -> None:
        self.input_details = self._interpreter.get_input_details()
        self.output_details = self._interpreter.get_output_details()

        self.waveform_input_index = self.input_details[0]['index']
        self.scores_output_index = self.output_details[0]['index']

        # Resize input tensor to match the expected duration
        input_shape = [self._recording_duration * self._sampling_rate]
        self._interpreter.resize_tensor_input(self.waveform_input_index, input_shape, strict=True)

        self._interpreter.allocate_tensors()

    def _load_class_names(self) -> List[str]:
        try:
            with open(self._class_map_path, 'r') as csv_file:
                class_map_csv = csv.reader(csv_file)
                next(class_map_csv)  # Skip header row
                return [row[2] for row in class_map_csv]  # Only display_name column
        except FileNotFoundError:
            self._logger.error(f"Class map file not found at {self._class_map_path}")
            return []

    def _get_top_class(self, scores: np.ndarray) -> Tuple[str, float]:
        mean_scores = scores.mean(axis=0)
        top_index = mean_scores.argmax()
        return self._class_names[top_index], mean_scores[top_index]

    def is_music_playing(self, waveform: np.ndarray) -> bool:
        if not self._class_names:
            self._logger.error("Class names are not loaded. Cannot perform detection.")
            return False

        self._interpreter.set_tensor(self.waveform_input_index, waveform)
        self._interpreter.invoke()

        scores = self._interpreter.get_tensor(self.scores_output_index)

        top_class, confidence = self._get_top_class(scores)
        return top_class == 'Music' and confidence > 0.2
