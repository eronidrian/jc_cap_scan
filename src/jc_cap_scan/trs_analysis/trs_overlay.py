import matplotlib.pyplot as plt
import argparse
import numpy as np

from jc_cap_scan.utils.trs_utils import load_trs_file


def get_alignment_offset(samples_valid: np.ndarray, samples_invalid: np.ndarray, alignment_threshold: float, align_to_start: bool) -> int | None:
    anchor_index = 0 if align_to_start else -1

    try:
        valid_anchor = np.where(samples_valid >= alignment_threshold)[0][anchor_index]
        invalid_anchor = np.where(samples_invalid >= alignment_threshold)[0][anchor_index]
    except IndexError:
        return None
    offset_invalid_x = valid_anchor - invalid_anchor

    return offset_invalid_x

def trs_overlay(path_valid: str, path_invalid: str, alignment_threshold: float, align_to_start: bool) -> None:

    samples_valid = load_trs_file(path_valid, True)
    samples_invalid = load_trs_file(path_invalid, True)

    offset_invalid_x = get_alignment_offset(samples_valid, samples_invalid, alignment_threshold, align_to_start)
    if offset_invalid_x is None:
        print("Traces cannot be aligned")
        return None

    fig, ax = plt.subplots()
    ax.plot(samples_valid, label=path_valid)
    ax.plot(range(offset_invalid_x, len(samples_invalid) + offset_invalid_x), samples_invalid,
            label=path_invalid)


    plt.xlabel("Sample number")
    plt.ylabel("Values")
    plt.legend(loc='upper left', )
    plt.show()

def main():
    parser = argparse.ArgumentParser(
        prog="TRS overlay",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("-v", "--valid", help="Path to trsfile which will be static", type=str, required=True)
    parser.add_argument("-i", "--invalid", help="Path to trsfile which will be moved", type=str, required=True)
    parser.add_argument("-a", "--alignment_threshold", help="Threshold for the alignment", type=float, required=True)
    parser.add_argument("--align_to_end", help="Align traces not to start but to end", action="store_true")

    args = parser.parse_args()
    trs_overlay(args.valid, args.invalid, args.alignment_threshold, not args.align_to_end)


if __name__ == '__main__':
   main()