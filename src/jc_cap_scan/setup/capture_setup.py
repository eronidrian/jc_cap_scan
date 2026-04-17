import argparse

from jc_cap_scan.config.config import CaptureConfig, Config
from jc_cap_scan.trs_analysis.trs_visualizer import visualize_trace
from jc_cap_scan.utils.capture_utils import capture_install_trace, capture_call_trace


def capture_sample_install_trace(trace_path: str, cap_file_path: str, estimated_config: CaptureConfig | None, show: bool, rescale: bool = False, auth: list[str] | None = None):
    config = estimated_config if estimated_config is not None else CaptureConfig.load_from_toml("") # or load some default config
    capture_install_trace(cap_file_path, 1, trace_path, config, auth)
    if show:
        visualize_trace(trace_path, 0, rescale)


def capture_sample_call_trace(trace_path: str, cap_file_path: str, estimated_config: CaptureConfig | None, show: bool, rescale: bool = False, auth: list[str] | None = None):
    config = estimated_config if estimated_config is not None else CaptureConfig.load_from_toml("") # or load some default config
    capture_call_trace(cap_file_path, 1, trace_path, config, auth)
    if show:
        visualize_trace(trace_path, 0, rescale)

def main():
    parser = argparse.ArgumentParser(
        prog="Setup trace capture"
    )

    call_or_install = parser.add_mutually_exclusive_group(required=True)
    call_or_install.add_argument('--install', help="Capture install trace", action='store_true')
    call_or_install.add_argument('--call', help="Capture call trace", action='store_true')
    parser.add_argument('--trs_file', help="File to store the trace", required=True, type=str)
    parser.add_argument('--cap_file', help="Path to CAP file to use for the capture.", required=True,
                                      type=str)
    parser.add_argument('--show', help="Whether to show the captured trace after capturing it",
                                      action='store_true', default=False)
    parser.add_argument('--config',
                                      help="Capture configuration file in toml format",
                                      required=False, type=str)
    parser.add_argument("--rescale", help="Rescale trace for visualization", action='store_true', default=False)
    parser.add_argument('--auth',
                        help="Authentication to use for the connection to the card. Enter as arguments to the GPPro, e.g. 'key' '1234567890' ('--' for the first item will be added automatically)",
                        type=str, nargs='+')

    args = parser.parse_args()

    config = CaptureConfig.load_from_toml(args.config)
    if args.auth is not None:
        args.auth[0] = f"--{args.auth[0]}"
    if args.install:
        capture_sample_install_trace(args.trs_file, args.cap_file, config, args.show, args.rescale, args.auth)
    if args.call:
        capture_sample_call_trace(args.trs_file, args.cap_file, config, args.show, args.rescale, args.auth)



if __name__ == '__main__':
     main()