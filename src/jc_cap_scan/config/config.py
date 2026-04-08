from __future__ import annotations
import tomllib


class ExtractionConfig:
    def __init__(self, max_gap: int, min_duration: int, threshold: int, index_to_extract: int):
        self.max_gap = max_gap
        self.min_duration = min_duration
        self.threshold = threshold
        self.index_to_extract = index_to_extract

    @staticmethod
    def load_from_toml(toml_path: str) -> ExtractionConfig:
        with open(toml_path, "rb") as f:
            content = tomllib.load(f)
        content = content["extraction"]

        return ExtractionConfig(content["max_gap"], content["min_duration"], content["threshold"],
                                content["index_to_extract"])


class CaptureConfig:
    def __init__(self, trigger_threshold: int, posttrigger_delay: int, number_of_samples: int, sample_interval: int,
                 channel_range: int):
        self.trigger_threshold = trigger_threshold
        self.posttrigger_delay = posttrigger_delay
        self.number_of_samples = number_of_samples
        self.sample_interval = sample_interval
        self.channel_range = channel_range

    @staticmethod
    def load_from_toml(toml_path: str) -> CaptureConfig:
        with open(toml_path, "rb") as f:
            content = tomllib.load(f)
        content = content["capture"]

        return CaptureConfig(content["trigger_threshold"], content["posttrigger_delay"],
                             content["number_of_samples"], content["sample_interval"], content["channel_range"])


class Config:
    def __init__(self, capture: CaptureConfig, extraction: ExtractionConfig):
        self.capture = capture
        self.extraction = extraction

    @staticmethod
    def load_from_toml(toml_path: str) -> Config:
        return Config(CaptureConfig.load_from_toml(toml_path), ExtractionConfig.load_from_toml(toml_path))
