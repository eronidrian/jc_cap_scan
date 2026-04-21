import matplotlib.pyplot as plt
import argparse
import numpy as np

from jc_cap_scan.utils.trs_utils import load_trs_file


def get_alignment_offset(samples_static: np.ndarray, samples_shift: np.ndarray, alignment_threshold: float, align_to_start: bool) -> int | None:
    """
    Get offset by which samples invalid should be shifted to align with samples valid
    :param samples_static: Array of samples that are fixed
    :param samples_shift: Array of samples that are shifted
    :param alignment_threshold: First sample above this threshold is considered as an 'anchor' that is aligned in both traces
    :param align_to_start: Whether to align traces to start
    :return: Offset for shifting the samples invalid, None if no such offset is found
    """
    anchor_index = 0 if align_to_start else -1

    try:
        static_anchor = np.where(samples_static >= alignment_threshold)[0][anchor_index]
        shift_anchor = np.where(samples_shift >= alignment_threshold)[0][anchor_index]
    except IndexError:
        return None
    offset_x = static_anchor - shift_anchor

    return offset_x

def trs_overlay(path_static: str, path_shift: str, alignment_threshold: float, align_to_start: bool) -> None:
    """
    Overlay two power traces
    :param path_static: Path to power trace that will be static
    :param path_shift: Path to power trace that will be moved
    :param alignment_threshold: Threshold for the alignment
    :param align_to_start: Whether to align traces to start
    :return:
    """
    samples_valid = load_trs_file(path_static, True)
    samples_invalid = load_trs_file(path_shift, True)

    offset_invalid_x = get_alignment_offset(samples_valid, samples_invalid, alignment_threshold, align_to_start)
    if offset_invalid_x is None:
        print("Traces cannot be aligned")
        return None

    fig, ax = plt.subplots()
    ax.plot(samples_valid, label=path_static)
    ax.plot(range(offset_invalid_x, len(samples_invalid) + offset_invalid_x), samples_invalid,
            label=path_shift)


    plt.xlabel("Sample number")
    plt.ylabel("Values")
    plt.legend(loc='upper left', )
    plt.show()

def main():
    parser = argparse.ArgumentParser(
        prog="TRS overlay",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--static", help="Path to trsfile which will be static", type=str, required=True)
    parser.add_argument("--shift", help="Path to trsfile which will be moved", type=str, required=True)
    parser.add_argument("-a", "--alignment_threshold", help="Threshold for the alignment", type=float, required=True)
    parser.add_argument("--align_to_end", help="Align traces not to start but to end", action="store_true")

    args = parser.parse_args()
    trs_overlay(args.valid, args.invalid, args.alignment_threshold, not args.align_to_end)


if __name__ == '__main__':
   main()