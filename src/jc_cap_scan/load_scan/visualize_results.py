import argparse
from typing import Literal
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib as mpl

from jc_cap_scan.utils.trs_utils import load_trs_file


def visualize_results(results_file: str, base_trace_path: str, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    """
    Visualize results of the LOAD scan
    :param results_file: Path to results file in CSV format
    :param base_trace_path: Path to the unchanged power trace
    :param show_or_save: Whether to show or save the plot. Possible values: 'show' and 'save'
    :param save_filename: Path to save the plot to if show_or_save is 'save'
    :return:
    """
    results = pd.read_csv(results_file, names=["component", "byte_number", "message", "diff"])
    results = results[results['message'] != "CAP loaded"] # include only successful installations

    base_trace = load_trs_file(base_trace_path, True)

    if show_or_save == 'save':
        mpl.use("pgf")
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
        })

    fig, ax = plt.subplots(2, 1, height_ratios=[2, 1], sharex=True)

    ax[1].plot(base_trace)
    ax[1].set_ylabel("Norm. power consumption")
    ax[1].set_xlabel("Sample number")

    sns.scatterplot(data = results, x="diff", y="byte_number", hue='component', style='component', ax=ax[0], zorder=1)
    ax[0].set_ylabel("Changed byte number")
    ax[0].legend()
    ax[0].set_title("LOAD scan results")

    plt.subplots_adjust(wspace=0, hspace=0)

    if show_or_save == 'show':
        plt.show()
    elif show_or_save == 'save':
        fig.tight_layout()
        fig.set_size_inches(w=5.00098, h=3.6)
        plt.savefig(save_filename, bbox_inches='tight')



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--results_file", help="Path to results file", type=str, required=True)
    parser.add_argument("--base_trace_path", help="Path to base power trace", type=str, required=True)
    parser.add_argument("--show_or_save", help="Whether to show or save the plot. Possible values: 'show' and 'save'", type=str, default="show")
    parser.add_argument("--save_filename", help="Filename to save the plot to, required if --show_or_save is 'save'", type=str, default=None)
    args  = parser.parse_args()

    visualize_results(args.results_file, args.base_trace_path, args.show_or_save, args.save_filename)

if __name__ == "__main__":
    main()
