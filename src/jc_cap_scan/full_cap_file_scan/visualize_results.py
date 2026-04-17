import argparse
from typing import Literal

import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib as mpl

from jc_cap_scan.utils.trs_utils import load_trs_file


def visualize_results(results_file: str, base_trace_path: str, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    results = pd.read_csv(results_file, names=["component", "byte_number", "message", "diff"])
    results = results[results['message'] != "CAP loaded"]

    base_trace = load_trs_file(base_trace_path, True)

    results['byte_number'] *= 0.1

    fig, ax = plt.subplots()
    ax.plot(base_trace)
    sns.scatterplot(data = results, x="diff", y="byte_number", hue='component', palette='deep')
    ax.legend(loc='upper right')

    if show_or_save == 'show':
        plt.show()
    elif show_or_save == 'save':
        mpl.use("pgf")
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
        })

        fig.tight_layout()
        fig.set_size_inches(w=5.00098, h=3.6)
        plt.savefig(save_filename)



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
