from __future__ import annotations
import tomllib
import numpy as np

from jc_cap_scan.utils.trs_utils import load_single_trace_from_trs_file

def normalize_template(template: np.ndarray):
    """
    Normalize template
    :param template: Template to normalize
    :return: Normalized template
    """
    template = template - template.mean()
    norm = np.linalg.norm(template)
    if norm == 0:
        raise ValueError("Template must not be constant")
    return template / norm


class ExtractionConfig:
    """
    Config used to extract duration information from the power trace
    """
    def __init__(self, template_filename: str, template_index: int, template_start: tuple[int, int], template_end: tuple[int, int]):
        """
        :param template_filename: Path to the TRS file to take the template from
        :param template_index: Index of the trace in the TRS file to use for the template
        :param template_start: Start and end sample for the template for the start of the extracted segment
        :param template_end: Start and end sample for the template for the end of the extracted segment
        """
        template_trace = load_single_trace_from_trs_file(template_filename, False, template_index)
        start_template = normalize_template(
            template_trace[template_start[0]:template_start[1]])
        end_template = normalize_template(
            template_trace[template_end[0]:template_end[1]])

        self.start_template = start_template
        self.end_template = end_template

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

        return ExtractionConfig(content["template_filename"], content["template_index"], content["template_start"],
                                content["template_end"])


class CaptureConfig:
    def __init__(self, autotrigger: int, posttrigger_delay: int, number_of_samples: int,
                 sample_interval: int, channel_range: int):
        """
        Config used to capture power traces
        :param autotrigger: in ms, artificially trigger after N ms
        :param posttrigger_delay: in ms, how long should the oscilloscope wait after receiving trigger for starting the capture
        :param number_of_samples: how many samples to capture
        :param sample_interval: in ns, interval between taking two samples
        :param channel_range: in mV, range of the Y-axis of the power trace
        """
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

        return CaptureConfig(content["autotrigger"], content["posttrigger_delay"],
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
