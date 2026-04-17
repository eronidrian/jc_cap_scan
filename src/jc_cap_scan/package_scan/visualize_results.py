import argparse
from typing import Literal

import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl

from jc_cap_scan.config.config import CaptureConfig
from jc_cap_scan.utils.capture_utils import get_actual_sample_interval


def visualize_results_discovery(result_file: str, capture_config: CaptureConfig, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    sample_interval = get_actual_sample_interval(capture_config.sample_interval)

    data = pd.read_csv(result_file)
    data = data.iloc[:, 1:]
    data = data.transpose()
    data.columns = [1, 2, 3, 4, 5, 6, 7, "major", "minor"]

    # convert to ms
    data = data.map(lambda x: (x * sample_interval) / 10 ** 6)

    # drop zero rows
    for i in data.index:
        if (data.loc[i, :] < 1).all():
            data.drop(i, inplace=True)

    fig, ax = plt.subplots()

    ax.boxplot(data, showfliers=False, tick_labels=list(data.columns))
    ax.set_xlabel("Changed byte")
    ax.set_ylabel("Duration [ms]")

    if show_or_save =='show':
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




def visualize_results_bruteforce(result_files: list[str], capture_config: CaptureConfig, highlight_values: list[int] | None, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    sample_interval = get_actual_sample_interval(capture_config.sample_interval)

    medians = pd.DataFrame()
    for result_file in result_files:
        data = pd.read_csv(result_file, names=[str(_) for _ in range(12)])
        data = data.iloc[:, 2:]
        data = data.transpose()


        data = data.map(lambda x: (x * sample_interval) / 10 ** 6)
        result_file = result_file.split("/")[-1].split(".")[0].split("_")[-1]
        medians[result_file] = data.median(axis=0)

    fig, ax = plt.subplots()
    ax.plot(medians, label=medians.columns)
    ax.set_xlabel("Value for xx")
    ax.set_ylabel("Median of LOAD processing duration [ms]")
    if highlight_values is not None:
        ax.vlines(highlight_values, ax.get_ylim()[0], ax.get_ylim()[1], 'gray', "dashed")
    plt.legend(loc="upper right", title="Base AID")
    ax.set_title("Results of package bruteforce")

    if show_or_save =='show':
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
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    bruteforce_or_discovery = parser.add_mutually_exclusive_group(required=True)
    bruteforce_or_discovery.add_argument('--discovery', action='store_true')
    bruteforce_or_discovery.add_argument('--bruteforce', action='store_true')
    parser.add_argument("--result_file", help="Path to result file. Can be multiple files for visualizing bruteforce results.", type=str, default=None, nargs='+')
    parser.add_argument("--capture_config", help="Path to capture config", type=str, required=True)
    parser.add_argument("--highlight_values", help="Values to highlight with vertical dashed lines, separated by space. Only for bruteforce results.", type=float, nargs='+')
    parser.add_argument("--show_or_save", help="Whether to show or save the plot. Possible values: 'show' and 'save'",
                        type=str, default="show")
    parser.add_argument("--save_filename", help="Filename to save the plot to, required if --show_or_save is 'save'",
                        type=str, default=None)
    args = parser.parse_args()

    capture_config = CaptureConfig.load_from_toml(args.capture_config)
    if args.discovery:
        visualize_results_discovery(args.result_file, capture_config, args.show_or_save, args.save_filename)
    elif args.bruteforce:
        visualize_results_bruteforce(args.result_file, capture_config, args.highlight_values, args.show_or_save, args.save_filename)

