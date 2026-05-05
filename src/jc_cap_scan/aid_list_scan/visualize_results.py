import argparse
from typing import Literal

import pandas as pd
from matplotlib import pyplot as plt
import matplotlib as mpl
import seaborn as sns

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
    data = pd.read_csv(results_file, index_col=[0, 2], names=[str(i) for i in range(1, 102)])
    data = data.transpose()
    data = data.map(lambda x: (x * sample_interval) / 10 ** 6)

    # print(data.head())

    meds = data.median()
    meds.sort_values(ascending=True, inplace=True)
    data = data[meds.index]

    if show_or_save == 'save':
        mpl.use("pgf")
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
        })

    fig, ax = plt.subplots()
    print(type(meds))
    print(list(meds))

    new_data = meds.reset_index()
    new_data.columns = ['aid', 'minor', 'median']
    new_data.sort_values(by='median', inplace=True)
    new_data['label'] = new_data.apply(lambda x: f"{x['aid']}: v1.{x['minor']}", axis=1)
    new_data['label'] = [
        "org.globalplatform (A00000015100): v1.1",
        "org.globalplatform: v1.0",
        "org.globalplatform: v1.2",
        "org.globalplatform: v1.3",
        "org.globalplatform: v1.5",
        "org.globalplatform: v1.6",
        "org.globalplatform: v1.4",
        "javacardx.external (A0000000620203): v1.0",
        "javacardx.crypto (A0000000620201): v1.1",
        "javacardx.crypto: v1.0",
        "javacardx.crypto: v1.3",
        "javacardx.crypto: v1.2",
        "javacardx.apdu (A0000000620209): v1.0",
        "javacard.security (A0000000620102): v1.0",
        "javacardx.crypto (A0000000620201): v1.4",
        "javacardx.crypto: v1.5",
        "javacardx.crypto: v1.6",
        "java.io (A0000000620002): v1.0",
        "java.lang (A0000000620001): v1.0",
    ]


    print(new_data)

    # ax.hist(data)
    # versions = [f"{column[0]}: v{column[1]}.{column[2]}" for column in data.columns]
    sns.scatterplot(new_data, y='label', x='median', hue='aid', legend=False, ax = ax)


    # ax.boxplot(data, showfliers=False)
    # ax.set_xticklabels(versions, rotation=45, ha='right')
    ax.set_ylabel("AID and version")
    ax.set_xlabel("Duration [ms]")
    ax.set_title("NXP JCOP 4 P71, package\_scan.4")



    if show_or_save == 'show':
        plt.tight_layout()
        plt.show()
    elif show_or_save == 'save':
        fig.tight_layout()
        fig.set_size_inches(w=5.00098, h=3.6)
        plt.savefig(save_filename, bbox_inches='tight')

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