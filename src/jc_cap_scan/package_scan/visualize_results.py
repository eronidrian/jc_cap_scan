import argparse
import csv
from typing import Literal

import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl

from jc_cap_scan.config.config import CaptureConfig
from jc_cap_scan.utils.capture_utils import get_actual_sample_interval


def load_data_discovery(result_file: str) -> pd.DataFrame:
    """
    Load data from the side channel discovery. Namely, merge the data for the same changed byte number
    :param result_file: Path to the CSV file with results
    :return: dataframe with preprocessed data
    """
    f = open(result_file, "r")
    csv_reader = csv.reader(f)
    data_dict = {}
    for row in csv_reader:
        byte_number, major, minor = row[1:4]
        measurements = list(map(int, row[4:]))
        major = int(major)
        minor = int(minor)
        if major == 1 and minor == 0:
            byte_number = int(byte_number)
            if data_dict.get(byte_number) is None:
                data_dict[byte_number] = measurements
            else:
                data_dict[byte_number].extend(measurements)
        elif major != 1:
            if data_dict.get('major') is None:
                data_dict['major'] = measurements
            else:
                data_dict['major'].extend(measurements)
        elif minor != 0:
            if data_dict.get('minor') is None:
                data_dict['minor'] = measurements
            else:
                data_dict['minor'].extend(measurements)

    data = pd.DataFrame.from_dict(data_dict)
    data = data.reindex(sorted(data.columns), axis=1)

    # data = pd.read_csv(result_file)
    # data = data.iloc[:, 1:]
    # data = data.transpose()
    # data.columns = [1, 2, 3, 4, 5, 6, 7, "major", "minor"]

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
    # convert to ms
    data = data.map(lambda x: (x * sample_interval) / 10 ** 6)

    # drop zero rows
    for i in data.index:
        if (data.loc[i, :] < 1).all():
            data.drop(i, inplace=True)

    fig, ax = plt.subplots()


    ax.boxplot(data, showfliers=False, tick_labels=list(data.columns))
    # ax.hist(data[data < 10])
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
        visualize_results_discovery(args.result_file[0], capture_config, args.show_or_save, args.save_filename)
    elif args.bruteforce:
        visualize_results_bruteforce(args.result_file, capture_config, args.highlight_values, args.show_or_save, args.save_filename)

if __name__ == "__main__":
    main()