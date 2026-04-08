import argparse
import sys

from matplotlib import pyplot as plt

from jc_cap_scan.config.config import ExtractionConfig, Config
from jc_cap_scan.trs_analysis.trs_extractor import find_high_consumption_periods
from jc_cap_scan.utils.trs_utils import load_trs_file


def extraction_setup(trs_file: str, config: ExtractionConfig, trace_index: int, show: bool):
    trace = load_trs_file(trs_file, True, trace_index)
    periods = find_high_consumption_periods(trace, config)
    print(periods)

    if show:
        fig, ax = plt.subplots()
        ax.plot(trace)
        ax.vlines(periods, ax.get_ylim()[0], ax.get_ylim()[1], 'r')
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
    main(sys.argv)