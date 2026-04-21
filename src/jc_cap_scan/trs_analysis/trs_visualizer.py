import argparse

import matplotlib.pyplot as plt

from jc_cap_scan.trs_analysis.trs_diff import load_trs_file


def visualize_trace(trs_file_path: str, trace_index: int, rescale: bool, start: int = 0, end: int = -1):
    """
    Visualize a power trace
    :param trs_file_path: Path to the TRS file to visualize
    :param trace_index: Index of trace int TRS file to visualize (0-indexed)
    :param rescale: Whether to rescale the trace using min-max standardization before plotting
    :param start: First sample to visualize (0-indexed)
    :param end: Last sample to visualize (0-indexed)
    :return:
    """
    trace = load_trs_file(trs_file_path, rescale, trace_index, start, end)

    fig, ax = plt.subplots()
    ax.plot(trace)
    ax.legend(loc='upper right')
    ax.set_xlabel("Sample number")
    ax.set_ylabel("Voltage" + "(rescaled)" if rescale else "[mV]")
    ax.set_title(f"Trace {trs_file_path}")
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS visualizer"
    )
    parser.add_argument("-f", "--trs_file", help="Path to .trs file", required=True)
    parser.add_argument("-i", "--trace_index", help="Index of trace to visualize. Default 0", required=False, default=0, type=int)
    parser.add_argument("--rescale", help="Rescale trace using min-max standardization", action="store_true")
    args = parser.parse_args()
    visualize_trace(args.trs_file, args.trace_index, args.rescale)