import trsfile
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import argparse
import numpy as np

def get_alignment_offset(samples_valid: np.ndarray, samples_invalid: np.ndarray, alignment_threshold: float, align_to_start: bool) -> int | None:
    anchor_index = 0 if align_to_start else -1

    # valid_average = np.average(samples_valid[:average_first])
    # invalid_average = np.average(samples_invalid[:average_first])
    # offset_invalid_y = valid_average - invalid_average

    try:
        valid_anchor = np.where(samples_valid >= alignment_threshold)[0][anchor_index]
        invalid_anchor = np.where(samples_invalid >= alignment_threshold)[0][anchor_index]
    except IndexError:
        return None
    offset_invalid_x = valid_anchor - invalid_anchor

    return offset_invalid_x

def trs_overlay():


    fig, ax = plt.subplots()



    alignment_threshold = 35
    align_to_start = True
    ignore_last = 1_000_000

    with trsfile.open(args.valid, 'r') as traces_valid:
        samples_valid = traces_valid[0].samples[:-ignore_last]

    with trsfile.open(args.invalid, 'r') as traces_invalid:
        samples_invalid = traces_invalid[0].samples[:-ignore_last]

    offset_invalid_x = get_alignment_offset(samples_valid, samples_invalid, alignment_threshold, align_to_start)
    if offset_invalid_x is None:
        return None

    ax.plot(samples_valid, label=args.valid)
    ax.plot(range(offset_invalid_x, len(samples_invalid) + offset_invalid_x), samples_invalid + offset_invalid_y,
            label=args.invalid)

    # if args.invalid_2:
    #     with trsfile.open(args.invalid_2, 'r') as traces_invalid:
    #         samples_invalid_2 = traces_invalid[0].samples[:-ignore_last]
    #
    #     invalid_anchor_2 = np.where(samples_invalid_2 >= alignment_threshold)[0][anchor_index]
    #     offset_invalid_2_x = valid_anchor - invalid_anchor_2
    #     invalid_average_2 = np.average(samples_invalid_2[:average_first])
    #     offset_invalid_2_y = valid_average - invalid_average_2
    #     ax.plot(range(offset_invalid_2_x, len(samples_invalid_2) + offset_invalid_2_x),
    #             samples_invalid_2 + offset_invalid_2_y,
    #             label=args.invalid_2)
    #
    # if args.invalid_3:
    #     with trsfile.open(args.invalid_3, 'r') as traces_invalid:
    #         samples_invalid_3 = traces_invalid[0].samples[:-ignore_last]
    #
    #     invalid_anchor_3 = np.where(samples_invalid_3 >= alignment_threshold)[0][anchor_index]
    #     offset_invalid_3_x = valid_anchor - invalid_anchor_3
    #     invalid_average_3 = np.average(samples_invalid_3[:average_first])
    #     offset_invalid_3_y = valid_average - invalid_average_3
    #     ax.plot(range(offset_invalid_3_x, len(samples_invalid_3) + offset_invalid_3_x),
    #             samples_invalid_3 + offset_invalid_3_y,
    #             label=args.invalid_3)



    plt.xlabel("Sample number")
    plt.ylabel("Values")
    plt.legend(loc='upper left', )
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS analyser",
        description=""
    )

    parser.add_argument('-v', '--valid', help='TRS file with valid LOAD', required=True)
    parser.add_argument('-i', '--invalid', help='TRS file with invalid LOAD', required=True)
    parser.add_argument('-i_2', '--invalid_2', help='Another TRS file with invalid LOAD', required=False)
    parser.add_argument('-i_3', '--invalid_3', help='Another TRS file with invalid LOAD', required=False)

    args = parser.parse_args()
    trs_overlay()