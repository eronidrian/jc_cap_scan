import argparse
import csv
from typing import Literal

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl
import seaborn as sns
from matplotlib.patches import Circle
from scipy.interpolate import CubicSpline

from jc_cap_scan.config.config import CaptureConfig
from jc_cap_scan.utils.capture_utils import get_actual_sample_interval
from jc_cap_scan.utils.stat_utils import normalize_by_buckets, data_to_one_column, limit_range

def merge_by_shorts(data: pd.DataFrame) -> pd.DataFrame:
    data = pd.DataFrame([pd.concat([data[1],data['maj.']], ignore_index=True).reset_index(drop=True),
                         pd.concat([data[2],data[3]], ignore_index=True).reset_index(drop=True),
                         pd.concat([data[4], data[5]], ignore_index=True).reset_index(drop=True),
                         pd.concat([data[6],data[7]], ignore_index=True).reset_index(drop=True),
                         data['min.'].reset_index(drop=True)])
    data = data.transpose()
    data.columns = ["1+maj.", "2+3", "4+5", "6+7", "min."]
    return data

def load_data_discovery(result_file: str) -> pd.DataFrame:
    """
    Load data from the side channel discovery. Namely, merge the data for the same changed byte number
    :param result_file: Path to the CSV file with results
    :return: dataframe with preprocessed data
    """
    # f = open(result_file, "r")
    # csv_reader = csv.reader(f)
    # data_dict = {}
    # for row in csv_reader:
    #     byte_number, major, minor = row[1:4]
    #     measurements = list(map(float, row[4:]))
    #     major = int(major)
    #     minor = int(minor)
    #     if major == 1 and minor == 0:
    #         byte_number = int(byte_number) + 1
    #     elif major != 1:
    #         byte_number = 20
    #     elif minor != 0:
    #         byte_number = 21
    #
    #     if data_dict.get(byte_number) is None:
    #         data_dict[byte_number] = measurements
    #     else:
    #         data_dict[byte_number].extend(measurements)
    #
    # data = pd.DataFrame.from_dict(data_dict)
    # data = data.reindex(sorted(data.columns), axis=1)
    # data.rename(columns={20: "maj.", 21: "min."}, inplace=True)

    data = pd.read_csv(result_file)
    data = data.iloc[:, 1:]
    data = data.transpose()
    data.columns = [1, 2, 3, 4, 5, 6, 7, "maj."]

    return data



def visualize_results_discovery(result_file: str, capture_config: CaptureConfig, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    """
    Visualize results from the side channel discovery
    :param result_file: Path to file with results
    :param capture_config: Capture config that has been used to capture the traces
    :param show_or_save: Whether to show or save the plot. Possible values: 'show' and 'save'
    :param save_filename: Path to save the plot to if show_or_save is 'save'
    :return:
    """
    data = load_data_discovery(result_file)
    sample_interval = get_actual_sample_interval(capture_config.sample_interval)
    print(sample_interval)
    # convert to ms
    data = data.map(lambda x: (x * 25.6) / 10 ** 6)
    # data = data.map(lambda x: x / 10 ** 6)

    # drop zero rows
    for i in data.index:
        if (data.loc[i, :] < 1).all():
            data.drop(i, inplace=True)

    # data = normalize_by_buckets(data, [(308, 311),(311, 314)])



    if show_or_save == 'save':
        mpl.use("pgf")
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
            # 'font.size': 1,
            "axes.titlesize": 20,
            "axes.labelsize": 15,
            "xtick.labelsize": 15,
            "ytick.labelsize": 15,
            "legend.fontsize": 15,
            "figure.titlesize": 25,
        })

    # data = data_to_one_column(data)
    # data = limit_range(data, 300, 400)
    # data = data.iloc[:, :7]
    medians = data.median(axis=0)
    # print(type(medians))
    # cs = CubicSpline(list(medians), np.arange(1, 8, 1))
    # xs = np.arange(1, 8, 0.1)

    fig, ax = plt.subplots()
    # sns.scatterplot(medians)
    # plt.plot([1, 9], [3.2382, 3.2451], color='gray', linestyle='--')
    # ax.plot(xs, cs(xs))
    # data = merge_by_shorts(data)

    sns.boxplot(data, showfliers=False)
    # ax.hist(data, bins=50)
    ax.set_xlabel("Changed byte")
    ax.set_ylabel("LOAD duration [ms]")
    ax.set_title("G\&D Smartcafe 6.0, package\_scan.1")

    if show_or_save =='show':
        plt.show()
    elif show_or_save == 'save':
        fig.tight_layout()
        fig.set_size_inches(w=5.00098, h=3.6)
        plt.savefig(save_filename, bbox_inches='tight')




def visualize_results_bruteforce(result_files: list[str], capture_config: CaptureConfig, highlight_values: list[int] | None, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    """
    Visualize results from the package bruteforce
    :param result_files: Path(s) to one or more files with the results
    :param capture_config: Capture config that has been used to capture the traces
    :param highlight_values: Value to highlight in the resulting plot
    :param show_or_save: Whetther
    :param save_filename:
    :return:
    """
    sample_interval = get_actual_sample_interval(capture_config.sample_interval)

    medians = pd.DataFrame()
    for result_file in result_files:
        data = pd.read_csv(result_file, names=[str(_) for _ in range(12)])
        data = data.iloc[:, 2:]
        data = data.transpose()


        data = data.map(lambda x: (x * 25.6) / 10 ** 6)
        result_file = result_file.split("/")[-1].split(".")[0].split("_")[-1]
        medians[result_file] = data.median(axis=0)

    if show_or_save == 'save':
        mpl.use("pgf")
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
            # 'font.size': 1,
            # "axes.titlesize": 20,
            # "axes.labelsize": 15,
            # "xtick.labelsize": 15,
            # "ytick.labelsize": 15,
            "legend.fontsize": 8,
            # "figure.titlesize": 25,
        })

    fig, ax = plt.subplots()
    a = sns.lineplot(medians)
    ax.set_xlabel("Value for xx")
    ax.set_ylabel("LOAD period duration median [ms]")
    # if highlight_values is not None:
        # ax.vlines(highlight_values, ax.get_ylim()[0], ax.get_ylim()[1], 'gray', "dashed")
    a.axes.plot([160], [6.6068], 'o', ms=8, mec='r', mfc='none')
    a.axes.plot([0], [6.6158], 'o', ms=8, mec='r', mfc='none')
    a.axes.plot([0], [6.6211], 'o', ms=8, mec='r', mfc='none')
    a.axes.plot([0], [6.626], 'o', ms=8, mec='r', mfc='none')
    a.axes.plot([98], [6.629], 'o', ms=8, mec='r', mfc='none')



    plt.legend(loc="upper right", title="Base AID")
    ax.set_title("Javacos A40, package\_scan.3")

    if show_or_save =='show':
        plt.show()
    elif show_or_save == 'save':
        fig.tight_layout()
        fig.set_size_inches(w=5.00098, h=3.6)
        plt.savefig(save_filename, bbox_inches='tight')

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
        visualize_results_discovery(args.result_file[0], capture_config, args.show_or_save, args.save_filename)
    elif args.bruteforce:
        visualize_results_bruteforce(args.result_file, capture_config, args.highlight_values, args.show_or_save, args.save_filename)

if __name__ == "__main__":
    main()