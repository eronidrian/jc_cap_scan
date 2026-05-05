import argparse
import random
from typing import Literal

import numpy as np
from matplotlib import pyplot as plt
from numpy import ndarray

from jc_cap_scan.config.config import ExtractionConfig
from jc_cap_scan.trs_analysis.trs_extractor import find_high_consumption_periods
from jc_cap_scan.trs_analysis.trs_overlay import get_alignment_offset
from jc_cap_scan.utils.trs_utils import load_trs_file


def ratio_diff(number_1: float, number_2: float) -> float:
    """
    Simple 'ratio diff'. Divide the bigger number by the smaller one.
    :param number_1: First number
    :param number_2: Second number
    :return: Ratio diff
    """
    if number_1 > number_2:
        return number_1 / number_2
    if number_2 > number_1:
        return number_2 / number_1
    return 1


def get_diff_periods(samples_valid: ndarray, samples_invalid: ndarray, threshold: float,
                     extraction_config: ExtractionConfig) -> float | None:
    """
    Get difference between two power traces by comparing the durations of extracted periods
    :param samples_valid: Array of valid samples (the base power trace)
    :param samples_invalid: Array of invalid samples (the compared power trace)
    :param threshold: How much longer or shorter should be a period be to be considered different
    :param extraction_config: Config to use for extracting the periods
    :return: Sample number of the first difference (random sample from the period) or None if no difference is found
    """
    periods_valid = find_high_consumption_periods(samples_valid, extraction_config)
    periods_invalid = find_high_consumption_periods(samples_invalid, extraction_config)
    # go through the periods and calculate differences
    for i in range(len(periods_valid)):
        if i >= len(periods_invalid):
            return None
        duration_valid = periods_valid[i][1] - periods_valid[i][0]
        duration_invalid = periods_invalid[i][1] - periods_invalid[i][0]
        diff = ratio_diff(duration_valid, duration_invalid)
        if diff > threshold:
            # return random sample in the period, fixes overlapping points
            return random.randrange(periods_valid[i][0], periods_valid[i][1])
    return None


def get_diff_subtraction(samples_valid: ndarray, samples_invalid: ndarray, diff_threshold: float, alignment_threshold: float, ignore_first_n: int,
                         show: bool) -> float | None:
    """
    Get difference of two power traces by aligning them and then subtracting the invalid from the valid one. The first sample where the absolute value of the diff is higher than the threshold is returned as the first difference.
    :param samples_valid: Array of valid samples (the base power trace)
    :param samples_invalid: Array of invalid samples (the compared power trace)
    :param diff_threshold: Threshold for the diff. The first sample where the absolute value of the diff is higher than this threshold is returned as the first difference.
    :param alignment_threshold: Threshold used to align the traces
    :param ignore_first_n: Do not look for difference in the first n samples
    :param show: Whether to show the plot with the valid, invalid and diff traces
    :return: Number of the first different sample, None if no difference is found
    """
    offset_invalid_x = get_alignment_offset(samples_valid, samples_invalid, alignment_threshold, True)
    if offset_invalid_x is None:
        return None

    start = int(offset_invalid_x)
    end = start + len(samples_invalid)

    # prepare diff array same length as valid
    diff = samples_valid.copy()

    # Case 1: invalid fully inside valid
    if start >= 0 and end <= len(samples_valid):
        diff[start:end] = samples_valid[start:end] - samples_invalid
    # Case 2: invalid starts before valid (clip left)
    elif start < 0 < end:
        left_clip = -start
        valid_slice = slice(0, min(end, len(samples_valid)))
        invalid_slice = slice(left_clip, left_clip + (valid_slice.stop - valid_slice.start))
        diff[valid_slice] = samples_valid[valid_slice] - (samples_invalid[invalid_slice])
    # Case 3: invalid starts inside but extends past valid (clip right)
    elif start < len(samples_valid) < end:
        valid_slice = slice(start, len(samples_valid))
        invalid_slice = slice(0, len(samples_valid) - start)
        diff[valid_slice] = samples_valid[valid_slice] - (samples_invalid[invalid_slice])
    # Case 4: invalid entirely outside valid -> no overlap
    else:
        # no overlap: diff is just the original valid (or you may want NaNs in non-overlap regions)
        pass

    # Optional: if you want diff only where overlap exists, set non-overlap to NaN
    overlap_start = max(0, start)
    overlap_end = min(len(samples_valid), end)
    mask = np.ones_like(diff, dtype=bool)
    mask[overlap_start:overlap_end] = False
    diff[mask] = np.nan

    diff = abs(diff)

    if show:
        fig, ax = plt.subplots()
        ax.plot(samples_valid, label='samples_valid')
        ax.plot(np.arange(start, end), samples_invalid, label='samples_invalid')
        ax.plot(diff, label='diff')
        ax.legend(loc='upper left')
        plt.show()

    if diff is None:
        return None
    diff = diff[ignore_first_n:]
    indices = np.where(diff >= diff_threshold)[0]
    if not indices.size:
        return None
    return indices[0] + ignore_first_n


def get_diff(path_valid: str, path_invalid: str, diff_threshold: float, alignment_threshold: float, algorithm: Literal['subtraction', 'periods'], show: bool, ignore_first_n : int | None = None,
             extraction_config: ExtractionConfig | None = None) -> float | None:
    """
    Get diff of two power traces using either the 'subtraction' or 'periods' algorithm
    :param path_valid: Path to valid trace (the base power trace)
    :param path_invalid: Path to invalid trace (the compared power trace)
    :param diff_threshold: Threshold to use for the diff
    :param alignment_threshold: Threshold used to align the traces (only for 'subtraction' algorithm)
    :param algorithm: Algorithm to use, can be either 'subtraction' or 'periods'
    :param show: Whether to show the diff (only for 'subtraction' algorithm)
    :param ignore_first_n: Ignore the first n samples when looking for the diff (only for 'subtraction' algorithm)
    :param extraction_config: Extraction config (only for the 'periods' algorithm)
    :return:
    """
    assert algorithm in ['subtraction', 'periods']

    samples_valid = load_trs_file(path_valid, True)
    samples_invalid = load_trs_file(path_invalid, True)

    if algorithm == 'subtraction':
        assert ignore_first_n is not None
        return get_diff_subtraction(samples_valid, samples_invalid, diff_threshold, alignment_threshold, ignore_first_n, show)
    elif algorithm == 'periods':
        assert extraction_config is not None
        return get_diff_periods(samples_valid, samples_invalid, diff_threshold, extraction_config)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS diff"
    )
    parser.add_argument("-v", "--valid", help="Path to trsfile which will be static", type=str, required=True)
    parser.add_argument("-i", "--invalid", help="Path to trsfile which will be moved", type=str, required=True)
    parser.add_argument("--diff_threshold", help="Threshold for the diff", type=float, required=True)
    parser.add_argument("--alignment_threshold", help="Threshold for the alignment", type=float, required=True)
    parser.add_argument("--ignore_first_n", help="Ignore first n samples (for 'subtraction' algorithm)", type=int, required=False, default=0)
    parser.add_argument("--show", help="Show the resulting plot", action="store_true", required=False)
    parser.add_argument("--algorithm", help="One of 'subtraction' or 'periods'", required=True)
    parser.add_argument("--config", help="Path to config for the 'periods' algorithm", required=False)

    args = parser.parse_args()

    if args.algorithm == 'subtraction':
        if args.show:
            get_diff(args.valid, args.invalid, args.diff_threshold, args.alignment_threshold, args.algorithm, True, args.ignore_first_n)
        elif not args.show:
            print(get_diff(args.valid, args.invalid, args.diff_threshold, args.alignment_threshold, args.algorithm, False, args.ignore_first_n))
    elif args.algorithm == 'periods':
        extraction_config = ExtractionConfig.load_from_toml(args.config)
        print(get_diff(args.valid, args.invalid, args.diff_threshold, args.alignment_treshold, args.algorithm, False, extraction_config=extraction_config))
