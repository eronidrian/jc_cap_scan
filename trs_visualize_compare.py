import trsfile
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS analyser",
        description=""
    )

    parser.add_argument('-v', '--valid', help='TRS file with valid LOAD', required=True)
    parser.add_argument('-i', '--invalid', help='TRS file with invalid LOAD', required=True)

    args = parser.parse_args()

    fig, ax = plt.subplots()
    offset_invalid_x = -2_842_000
    offset_invalid_y = 0

    highlight_start = 10_518_000
    highlight_end = 10_763_000

    with trsfile.open(args.valid, 'r') as traces_valid:
        samples_valid = traces_valid[0].samples

    with trsfile.open(args.invalid, 'r') as traces_invalid:
        samples_invalid = traces_invalid[0].samples

    # times = np.arange(len(samples_valid)) * 25.6 / 10**6
    ax.plot(samples_valid, label="Successful LOAD")
    ax.plot(range(offset_invalid_x, len(samples_invalid) + offset_invalid_x), samples_invalid + offset_invalid_y,
            label="Unsuccessful LOAD")
    ax.add_patch(Rectangle((highlight_start, ax.get_ylim()[0]), highlight_end - highlight_start,
                           abs(ax.get_ylim()[0] - ax.get_ylim()[1]), facecolor="xkcd:pale pink", label="Measurement range"))

    plt.xlabel("Sample number")
    plt.ylabel("Values")
    plt.legend(loc='upper left', )
    plt.show()
