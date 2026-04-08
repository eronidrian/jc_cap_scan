import pandas as pd
import trsfile
from matplotlib import pyplot as plt
import seaborn as sns

from jc_cap_scan.utils.trs_utils import load_trs_file


def visualize_results(results_file: str, base_trace_path: str) -> None:
    results = pd.read_csv(results_file, names=["component", "byte_number", "message", "diff"])
    results = results[results['message'] != "CAP loaded"]
    # print(results.to_string())

    base_trace = load_trs_file(base_trace_path, True)

    results['byte_number'] += 50

    fig, ax = plt.subplots()
    ax.plot(base_trace)
    sns.scatterplot(data = results, x="diff", y="byte_number", hue='component', palette='deep')
    ax.legend(loc='upper right')
    plt.show()

if __name__ == '__main__':
    visualize_results("/home/petr/Downloads/diplomka/load_scan_results/results_javacos.csv", "/home/petr/Downloads/diplomka/load_scan_results/traces_javacos/base_install_resampled_2000.trs")

