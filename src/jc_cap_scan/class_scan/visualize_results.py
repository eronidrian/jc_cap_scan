import argparse
from typing import Literal
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl


from jc_cap_scan.config.config import CaptureConfig
from jc_cap_scan.utils.capture_utils import get_actual_sample_interval


def visualize_results(result_file: str, capture_config: CaptureConfig, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    """
    Visualise results of the class side channel discovery
    :param result_file: Path to result file in CSV format
    :param capture_config: Config that was used to capture results
    :param show_or_save: Whether to show or save the plot. Possible values: 'show' and 'save'
    :param save_filename: Where to save the plot if show_or_save is 'save'
    :return:
    """

    sample_interval = get_actual_sample_interval(capture_config.sample_interval)
    data = pd.read_csv(result_file, names=[str(_) for _ in range(12)])
    data = data.iloc[:, 1:]
    data = data.transpose()
    data = data.map(lambda x: (x * sample_interval) / 10 ** 6)

    if show_or_save == 'save':
        mpl.use("pgf")
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
        })

    fig, ax = plt.subplots()
    ax.boxplot(data, showfliers=False)
    ax.set_xlabel("Class token")
    ax.set_ylabel("Median of LOAD processing duration [ms]")
    ax.set_title("Results of class side channel discovery")

    if show_or_save =='show':
        plt.show()
    elif show_or_save == 'save':
        fig.tight_layout()
        fig.set_size_inches(w=5.00098, h=3.6)
        plt.savefig(save_filename)

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--result_file", help="Path to result file.", type=str)
    parser.add_argument("--capture_config", help="Path to capture config", type=str, required=True)
    parser.add_argument("--show_or_save", help="Whether to show or save the plot. Possible values: 'show' and 'save'",
                        type=str, default="show")
    parser.add_argument("--save_filename", help="Filename to save the plot to, required if --show_or_save is 'save'",
                        type=str, default=None)
    args = parser.parse_args()

    capture_config = CaptureConfig.load_from_toml(args.capture_config)
    visualize_results(args.result_file, capture_config, args.show_or_save, args.save_filename)

if __name__ == "__main__":
    main()