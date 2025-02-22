import csv
import numpy as np
from tflite_runtime.interpreter import Interpreter
from typing import List, Tuple
from python.logger import Logger


class MusicDetectionService:
    def __init__(self, recording_duration: int, model_path: str = 'python/ml-model/1.tflite',
                 class_map_path: str = 'python/ml-model/yamnet_class_map.csv') -> None:
        self.logger = Logger().get_logger()
        self.recording_duration = recording_duration
        self.sampling_rate = 16000
        self.model_path = model_path
        self.class_map_path = class_map_path

        self.interpreter = Interpreter('python/ml-model/1.tflite')
        self._configure_interpreter()

        self.class_names = self._load_class_names()

    def _configure_interpreter(self) -> None:
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        self.waveform_input_index = self.input_details[0]['index']
        self.scores_output_index = self.output_details[0]['index']

        # Resize input tensor to match the expected duration
        input_shape = [self.recording_duration * self.sampling_rate]
        self.interpreter.resize_tensor_input(self.waveform_input_index, input_shape, strict=True)

        self.interpreter.allocate_tensors()

    def _load_class_names(self) -> List[str]:
        try:
            with open(self.class_map_path, 'r') as csv_file:
                class_map_csv = csv.reader(csv_file)
                next(class_map_csv)  # Skip header row
                return [row[2] for row in class_map_csv]  # Only display_name column
        except FileNotFoundError:
            self.logger.error(f"Class map file not found at {self.class_map_path}")
            return []

    def _get_top_class(self, scores: np.ndarray) -> Tuple[str, float]:
        mean_scores = scores.mean(axis=0)
        top_index = mean_scores.argmax()
        return self.class_names[top_index], mean_scores[top_index]

    def is_music_playing(self, waveform: np.ndarray) -> bool:
        if not self.class_names:
            self.logger.error("Class names are not loaded. Cannot perform detection.")
            return False

        self.interpreter.set_tensor(self.waveform_input_index, waveform)
        self.interpreter.invoke()

        scores = self.interpreter.get_tensor(self.scores_output_index)

        top_class, confidence = self._get_top_class(scores)
        return top_class == 'Music' and confidence > 0.2
