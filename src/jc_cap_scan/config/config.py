from __future__ import annotations
import tomllib


class ExtractionConfig:
    """
    Config used to extract duration information from the power trace
    """
    def __init__(self, max_gap: int, min_duration: int, threshold: int, index_to_extract: int):
        """
        :param max_gap: max gap between two periods that is bridged to merge them into a single period
        :param min_duration: periods shorter than this threshold are discarded
        :param threshold: threshold for detecting raising and falling edges for starts and ends of the periods
        :param index_to_extract: period number that is important for the measurement
        """
        self.max_gap = max_gap
        self.min_duration = min_duration
        self.threshold = threshold
        self.index_to_extract = index_to_extract

    @staticmethod
    def load_from_toml(toml_path: str) -> ExtractionConfig:
        """
        Load extraction configuration from a TOML file
        :param toml_path: Path to the TOML file
        :return: Extraction configuration
        """
        with open(toml_path, "rb") as f:
            content = tomllib.load(f)
        content = content["extraction"]

        return ExtractionConfig(content["max_gap"], content["min_duration"], content["threshold"],
                                content["index_to_extract"])


class CaptureConfig:
    def __init__(self, trigger_threshold: int, autotrigger: int, posttrigger_delay: int, number_of_samples: int,
                 sample_interval: int, channel_range: int):
        """
        Config used to capture power traces
        :param trigger_threshold: in mV, after reaching what threshold should the capture start
        :param autotrigger: in ms, artificially trigger after N ms
        :param posttrigger_delay: in ms, how long should the oscilloscope wait after receiving trigger for starting the capture
        :param number_of_samples: how many samples to capture
        :param sample_interval: in ns, interval between taking two samples
        :param channel_range: in mV, range of the Y-axis of the power trace
        """
        self.trigger_threshold = trigger_threshold
        self.posttrigger_delay = posttrigger_delay
        self.autotrigger = autotrigger
        self.number_of_samples = number_of_samples
        self.sample_interval = sample_interval
        self.channel_range = channel_range

    @staticmethod
    def load_from_toml(toml_path: str) -> CaptureConfig:
        """
        Load capture configuration from a TOML file
        :param toml_path: Path to the TOML file
        :return: Capture configuration
        """
        with open(toml_path, "rb") as f:
            content = tomllib.load(f)
        content = content["capture"]

        return CaptureConfig(content["trigger_threshold"], content["autotrigger"], content["posttrigger_delay"],
                             content["number_of_samples"], content["sample_interval"], content["channel_range"])


class Config:
    """
    Config used to capture and process power traces for a given card
    """
    def __init__(self, capture: CaptureConfig, extraction: ExtractionConfig):
        """
        :param capture: Capture configuration
        :param extraction: Extraction configuration
        """
        self.capture = capture
        self.extraction = extraction

    @staticmethod
    def load_from_toml(toml_path: str) -> Config:
        """
        Load config from the TOML file
        :param toml_path: Path to the TOML file
        :return: Config
        """
        return Config(CaptureConfig.load_from_toml(toml_path), ExtractionConfig.load_from_toml(toml_path))
