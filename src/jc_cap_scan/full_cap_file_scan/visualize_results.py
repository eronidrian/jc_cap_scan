import argparse
import csv
from typing import Literal

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib as mpl
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
from scipy.interpolate import interp1d

from jc_cap_scan.utils.trs_utils import load_trs_file


def upsample_column(col, bucket_indices, bucket_size, trace_length):
    """
    Upsample a single column (Series) to match trace length.

    Parameters:
    -----------
    col : pd.Series
        Column from bucketed DataFrame
    bucket_indices : array
        Bin edge values (index of the DataFrame)
    bucket_size : int
        Size of each bucket
    trace_length : int
        Target length

    Returns:
    --------
    pd.Series
        Upsampled column
    """

    bucket_x = bucket_indices.astype(float) + bucket_size / 2
    interp_func = interp1d(bucket_x, col.values, kind='linear',
                           bounds_error=False, fill_value='extrapolate')
    upsampled = np.maximum(interp_func(np.arange(trace_length)), 0)

    return pd.Series(upsampled)

def visualize_results(results_file: str, base_trace_path: str, show_or_save: Literal['show', 'save'], save_filename: str | None = None) -> None:
    """
    Visualize results of the full CAP file scan
    :param results_file: Path to results file in CSV format
    :param base_trace_path: Path to the unchanged power trace
    :param show_or_save: Whether to show or save the plot. Possible values: 'show' and 'save'
    :param save_filename: Path to save the plot to if show_or_save is 'save'
    :return:
    """
    # f = open(results_file, 'r')
    # csv_reader = csv.reader(f)
    #
    # data_dict = {}
    # for row in csv_reader:
    #     component = row[0]
    #     message = row[2]
    #     if row[3] == '':
    #         continue
    #     diff = float(row[3])
    #     if message == "CAP loaded":
    #         continue
    #     if data_dict.get(component) is None:
    #         data_dict[component] = [diff]
    #     else:
    #         data_dict[component].append(diff)
    #
    # # print(data_dict)
    # results = pd.DataFrame.from_dict(data_dict, orient='index').transpose()
    # bins = [_ for _ in range(0, 4_000_000, 3000)]
    # buckets = results.apply(lambda col: pd.cut(col, bins=bins, labels=bins[:-1]).value_counts().sort_index())
    #
    # buckets = buckets.apply(
    #     upsample_column,
    #     bucket_indices=buckets.index.values,
    #     bucket_size=3000,
    #     trace_length=4_000_000
    # )
    #
    #
    # fig, axes = plt.subplots(7, 1, figsize=(12, 6), sharex=True)
    #
    # for i, column_name in enumerate(buckets.columns):
    #     data = buckets[column_name].to_numpy()
    #     data_2d = data.reshape(1, -1)
    #     ax = axes[i]
    #     im = ax.imshow(data_2d, cmap='hot', aspect='auto')
    #
    #     # ax.set_yticks([])
    #     ax.set_ylabel(column_name, fontweight='bold', fontsize=10)
    #
    #     # Add colorbar for each
    #     # cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.08)
    #     # cbar.ax.tick_params(labelsize=8)
    #
    # base_trace = load_trs_file(base_trace_path, True)
    # axes[-1].plot(base_trace[:4_000_000])
    # # axes[-1].set_xlabel('Index', fontsize=10)
    # plt.tight_layout()
    # plt.show()

    results = pd.read_csv(results_file, names=["component", "byte_number", "message", "diff"])
    results = results[results['message'] != "CAP loaded"]

    print(results.head())
    results = results.loc[results['component'].isin(['Header', 'Import', 'ConstantPool', 'RefLocation', 'Class', 'StaticField'])]


    base_trace = load_trs_file(base_trace_path, True)

    # results['byte_number'] *= 0.05
    # results['byte_number'] += 1

    if show_or_save == 'save':
        mpl.use("pgf")
        mpl.rcParams.update({
            "pgf.texsystem": "pdflatex",
            'font.family': 'serif',
            'text.usetex': True,
            'pgf.rcfonts': False,
            # 'font.size':22
        })


    fig, ax = plt.subplots(2, 1, height_ratios=[2, 1], sharex=True)
    # sns.lineplot(base_trace, ax=ax[1])
    ax[1].plot(base_trace)
    ax[1].set_ylabel("Norm. power consumption")
    ax[1].set_xlim(6_700_000, 10_000_000)
    ax[1].set_xlabel("Sample number")


    sns.scatterplot(data = results, x="diff", y="byte_number", hue='component', style='component', palette=['tab:blue', 'tab:orange', 'tab:green', 'tab:brown', 'tab:gray', 'tab:pink'], markers =['o', 'X', (4,0,45), (4,1,0), 'v', '^'], ax=ax[0], zorder=1)
    ax[0].set_ylabel("Changed byte number")
    ax[0].legend()
    ax[0].set_title("G\&D Smartcafe 6.0, load\_scan")

    for i in range(2):
        ax[i].add_patch(Rectangle((6_780_000, ax[i].get_ylim()[0]), 6_910_000 - 6_780_000,
                                  abs(ax[i].get_ylim()[0] - ax[i].get_ylim()[1]), edgecolor="tab:blue", fill=False
                                  ,zorder=0))
        ax[i].add_patch(Rectangle((8_252_000, ax[i].get_ylim()[0]), 8_423_000 - 8_252_000,
                                  abs(ax[i].get_ylim()[0] - ax[i].get_ylim()[1]), edgecolor="tab:orange", fill=False,
                                  zorder=0))
        ax[i].add_patch(Rectangle((8_760_000, ax[i].get_ylim()[0]), 9_035_000 - 8_760_000,
                                  abs(ax[i].get_ylim()[0] - ax[i].get_ylim()[1]), edgecolor="tab:brown", fill=False,
                                  zorder=0))
        ax[i].add_patch(Rectangle((9_332_000, ax[i].get_ylim()[0]), 9_454_000 - 9_332_000,
                                  abs(ax[i].get_ylim()[0] - ax[i].get_ylim()[1]), edgecolor="tab:green", fill=False,
                                  zorder=0))
        ax[i].add_patch(Rectangle((9_325_000, ax[i].get_ylim()[0]), 9_460_000 - 9_325_000,
                                  abs(ax[i].get_ylim()[0] - ax[i].get_ylim()[1]), edgecolor="tab:gray", fill=False,
                                  zorder=0))
        ax[i].add_patch(Rectangle((9_580_000, ax[i].get_ylim()[0]), 9_724_000 - 9_580_000,
                                  abs(ax[i].get_ylim()[0] - ax[i].get_ylim()[1]), edgecolor="tab:pink", fill=False,
                                  zorder=0))

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
