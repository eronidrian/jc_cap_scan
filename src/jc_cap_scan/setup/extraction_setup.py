import argparse
import sys

from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle

from jc_cap_scan.config.config import ExtractionConfig, Config
from jc_cap_scan.trs_analysis.trs_extractor import find_high_consumption_periods
from jc_cap_scan.utils.trs_utils import load_trs_file


def extraction_setup(trs_file: str, extraction_config: ExtractionConfig, trace_index: int, show: bool):
    """
    Try extraction of time from a power trace
    :param trs_file: TRS file to extract the time
    :param extraction_config: Configuration for the extraction
    :param trace_index: Index of the trace from the TRS file to use
    :param show: Whether to show the trace with found periods or not
    :return:
    """
    trace = load_trs_file(trs_file, True, trace_index)
    periods = find_high_consumption_periods(trace, extraction_config)
    print(periods)
    print(len(periods))

    if show:
        fig, ax = plt.subplots()
        ax.plot(trace)
        ax.vlines(periods, ax.get_ylim()[0], ax.get_ylim()[1], 'r')
        if len(periods) > extraction_config.index_to_extract:
            highlight_start = periods[extraction_config.index_to_extract][0]
            highlight_end = periods[extraction_config.index_to_extract][1]
            ax.add_patch(Rectangle((highlight_start, ax.get_ylim()[0]), highlight_end - highlight_start,
                                   abs(ax.get_ylim()[0] - ax.get_ylim()[1]), facecolor="xkcd:lightgreen"))
        ax.set_xlabel("Sample number")
        ax.set_ylabel("Voltage (rescaled)")
        ax.set_title(f"Trace {trs_file}, index: {trace_index}")
        plt.show()


def main(argv: list[str]):
    parser = argparse.ArgumentParser(
        prog="Setup time extraction"
    )


    parser.add_argument('--trs_file', help="Path to the .trs file to extract the times from",
                                         required=True, type=str)
    parser.add_argument('--config', help="Extraction configuration file in toml format", required=True,
                                         type=str)
    parser.add_argument('--trace_index', help="Index of the trace from .trs file to use", required=False, default=0, type=int)
    parser.add_argument('--show', help='Show trace with found periods', action='store_true')

    args = parser.parse_args(argv)

    config = ExtractionConfig.load_from_toml(args.config)
    extraction_setup(args.trs_file, config, args.trace_index, args.show)

if __name__ == '__main__':
    main(sys.argv[1:])