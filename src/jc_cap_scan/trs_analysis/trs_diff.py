import argparse

import numpy as np
import trsfile
from matplotlib import pyplot as plt
from numpy import ndarray

from jc_cap_scan.trs_analysis.trs_overlay import get_alignment_parameters

align_to_start = True
anchor_index = 0 if align_to_start else -1
alignment_threshold = 30
align_to_start = True
ignore_last = 1_000_000
average_first = 10_000


def get_diff(path_1: str, path_2: str, show: bool) -> ndarray | None:
    with trsfile.open(path_1, 'r') as traces_valid:
        samples_valid = traces_valid[0].samples[:-ignore_last]

    with trsfile.open(path_2, 'r') as traces_invalid:
        samples_invalid = traces_invalid[0].samples[1_000_000:-ignore_last]

    offset_invalid_x, offset_invalid_y = get_alignment_parameters(samples_valid, samples_invalid, alignment_threshold, average_first, True)
    if offset_invalid_x is None:
        return None

    start = int(offset_invalid_x)
    end = start + len(samples_invalid)

    # prepare diff array same length as valid
    diff = samples_valid.copy()  # or np.empty_like(samples_valid) if you will overwrite all values

    # Case 1: invalid fully inside valid
    if start >= 0 and end <= len(samples_valid):
        diff[start:end] = samples_valid[start:end] - (samples_invalid + offset_invalid_y)
    # Case 2: invalid starts before valid (clip left)
    elif start < 0 < end:
        left_clip = -start
        valid_slice = slice(0, min(end, len(samples_valid)))
        invalid_slice = slice(left_clip, left_clip + (valid_slice.stop - valid_slice.start))
        diff[valid_slice] = samples_valid[valid_slice] - (samples_invalid[invalid_slice] + offset_invalid_y)
    # Case 3: invalid starts inside but extends past valid (clip right)
    elif start < len(samples_valid) < end:
        valid_slice = slice(start, len(samples_valid))
        invalid_slice = slice(0, len(samples_valid) - start)
        diff[valid_slice] = samples_valid[valid_slice] - (samples_invalid[invalid_slice] + offset_invalid_y)
    # Case 4: invalid entirely outside valid -> no overlap
    else:
        # no overlap: diff is just the original valid (or you may want NaNs in non-overlap regions)
        pass

    # Optional: if you want diff only where overlap exists, set non-overlap to NaN
    overlap_start = max(0, start)
    overlap_end = min(len(samples_valid), end)
    mask = np.ones_like(diff, dtype=bool)
    mask[overlap_start:overlap_end] = False
    diff[mask] = np.nan  # or leave as original values

    if show:
        fig, ax = plt.subplots()
        ax.plot(samples_valid, label=path_1)
        ax.plot(range(start, end), samples_invalid + offset_invalid_y, label=path_2)
        ax.plot(abs(diff), label='diff')
        ax.legend(loc='upper left')
        plt.show()

    return abs(diff)

def get_first_difference(path_1: str, path_2: str, threshold: int) -> int | None:
    diff = get_diff(path_1, path_2, False)
    if diff is None:
        return None
    return np.where(diff >= threshold)[0][0]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS diff"
    )
    parser.add_argument("-v", "--valid", help="Path to trsfile which will be static", type=str, required=True)
    parser.add_argument("-i", "--invalid", help="Path to trsfile which will be moved", type=str, required=True)
    parser.add_argument("-t", "--threshold", help="Threshold for the diff", type=int)
    parser.add_argument("--show", help="Show the resulting plot", action="store_true", required=False)

    args = parser.parse_args()

    if args.show:
        get_diff(args.valid, args.invalid, True)
    elif not args.show:
        print(get_first_difference(args.valid, args.invalid, args.threshold))
