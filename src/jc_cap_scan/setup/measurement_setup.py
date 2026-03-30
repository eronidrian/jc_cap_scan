from jc_cap_scan.config.config import MeasurementConfig
from jc_cap_scan.trs_analysis.trs_visualizer import visualize_trace
from jc_cap_scan.utils.measurement_utils import measure_cap_file_install, measure_cap_file_call


def capture_sample_install_trace(trace_path: str, cap_file_path: str, estimated_config: MeasurementConfig | None, show: bool, auth):
    config = estimated_config if estimated_config is not None else MeasurementConfig.load_from_toml("") # or load some default config
    measure_cap_file_install(cap_file_path, 1, trace_path, config, auth)
    if show:
        visualize_trace(trace_path, 0)


def capture_sample_call_trace(trace_path: str, cap_file_path: str, estimated_config: MeasurementConfig | None, show: bool, auth):
    config = estimated_config if estimated_config is not None else MeasurementConfig.load_from_toml("") # or load some default config
    measure_cap_file_call(cap_file_path, 1, trace_path, config, auth)
    if show:
        visualize_trace(trace_path, 0)