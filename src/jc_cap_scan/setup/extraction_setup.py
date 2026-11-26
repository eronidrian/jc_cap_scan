import argparse
from matplotlib import pyplot as plt

from jc_cap_scan.config.config import ExtractionConfig
from jc_cap_scan.trs_analysis.trs_extractor import find_segment_start_and_end_in_trace
from jc_cap_scan.utils.trs_utils import load_single_trace_from_trs_file


def extraction_setup(trs_file: str, extraction_config: ExtractionConfig, trace_index: int, show: bool):
    """
    Try extraction of time from a power trace
    :param trs_file: TRS file to extract the time
    :param extraction_config: Configuration for the extraction
    :param trace_index: Index of the trace from the TRS file to use
    :param show: Whether to show the trace with found periods or not
    :return:
    """
    trace = load_single_trace_from_trs_file(trs_file, False, trace_index)
    start_start, start_end, end_start, end_end = find_segment_start_and_end_in_trace(trace, extraction_config.start_template, extraction_config.end_template)
    print(start_start, start_end, end_start, end_end)
    print(end_start - start_end)

    if show:
        fig, ax = plt.subplots()
        ax.plot(trace)
        ax.vlines([start_start, start_end], ax.get_ylim()[0], ax.get_ylim()[1], 'r')
        ax.vlines([end_start, end_end], ax.get_ylim()[0], ax.get_ylim()[1], 'g')

        # highlight extracted region if it is in range
        ax.set_xlabel("Sample number")
        ax.set_ylabel("Voltage")
        ax.set_title(f"Trace {trs_file}, index: {trace_index}")
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        prog="Setup time extraction"
    )


    parser.add_argument('--trs_file', help="Path to the .trs file to extract the times from",
                                         required=True, type=str)
    parser.add_argument('--config', help="Extraction configuration file in toml format", required=True,
                                         type=str)
    parser.add_argument('--trace_index', help="Index of the trace from .trs file to use", required=False, default=0, type=int)
    parser.add_argument('--show', help='Show trace with found periods', action='store_true')

    args = parser.parse_args()

    config = ExtractionConfig.load_from_toml(args.config)
    extraction_setup(args.trs_file, config, args.trace_index, args.show)

if __name__ == '__main__':
    main()