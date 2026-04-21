import argparse
from typing import Literal

import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl

from jc_cap_scan.config.config import CaptureConfig
from jc_cap_scan.utils.capture_utils import get_actual_sample_interval


def visualize_results(results_file: str, capture_config: CaptureConfig, show_or_save: Literal["show", "save"], save_filename: str | None = None):
    """
    Visualise the results of the AID list scan
    :param results_file: Path to results file in CSV format
    :param capture_config: Path to config, that has been used to capture results
    :param show_or_save: Whether to show or save the plot. Possible values: 'show' and 'save'
    :param save_filename: Where to save the plot, required if show_or_save is 'save'
    :return:
    """
    sample_interval = get_actual_sample_interval(capture_config.sample_interval)
    data = pd.read_csv(results_file, index_col=[0, 1, 2], names=[str(i) for i in range(1, 101)])
    data = data.transpose()
    data = data.map(lambda x: (x * sample_interval) / 10 ** 6)


    meds = data.median()
    meds.sort_values(ascending=True, inplace=True)
    data = data[meds.index]

    fig, ax = plt.subplots()

    # ax.hist(data)
    versions = [f"...{column[0][8:]}: v{column[1]}.{column[2]}" for column in data.columns]
    ax.boxplot(data, showfliers=False)
    ax.set_xticklabels(versions, rotation=45, ha='right')
    ax.set_xlabel("AID and version")
    ax.set_ylabel("Duration [ms]")

    if show_or_save == 'show':
        plt.tight_layout()
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
    parser.add_argument("--capture_config", help="Path to capture config", type=str, required=True)
    parser.add_argument("--show_or_save", help="Whether to show or save the plot. Possible values: 'show' and 'save'", type=str, default="show")
    parser.add_argument("--save_filename", help="Filename to save the plot to, required if --show_or_save is 'save'", type=str, default=None)
    args = parser.parse_args()

    capture_config = CaptureConfig.load_from_toml(args.capture_config)
    visualize_results(args.results_file, capture_config, args.show_or_save, args.save_filename)

if __name__ == "__main__":
    main()