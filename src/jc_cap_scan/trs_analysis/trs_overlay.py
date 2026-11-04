import matplotlib.pyplot as plt
import argparse
import numpy as np

from jc_cap_scan.config.config import ExtractionConfig
from jc_cap_scan.trs_analysis.trs_extractor import find_template_in_trace, normalize_template
from jc_cap_scan.utils.trs_utils import load_trs_file


def get_alignment_offset(samples_static: np.ndarray, samples_shift: np.ndarray, template: np.ndarray) -> int | None:
    """
    Get offset by which samples invalid should be shifted to align with samples valid
    :param samples_static: Array of samples that are fixed
    :param samples_shift: Array of samples that are shifted
    :param template: Normalized template used to aling the traces
    :return: Offset for shifting the samples invalid
    """
    static_anchor, _ = find_template_in_trace(samples_static, template)
    shift_anchor, _ = find_template_in_trace(samples_shift, template)

    offset_x = static_anchor - shift_anchor

    return offset_x

def trs_overlay(path_static: str, path_shift: str, extraction_config: ExtractionConfig) -> None:
    """
    Overlay two power traces
    :param path_static: Path to power trace that will be static
    :param path_shift: Path to power trace that will be moved
    :param extraction_config: Extraction configuration for getting information about template
    :return:
    """
    samples_valid = load_trs_file(path_static, False)
    samples_invalid = load_trs_file(path_shift, False)

    template_trace = load_trs_file(extraction_config.template_filename, False, extraction_config.template_index)
    template = normalize_template(
        template_trace[extraction_config.template_start[0]:extraction_config.template_start[1]])

    offset_invalid_x = get_alignment_offset(samples_valid, samples_invalid, template)
    if offset_invalid_x is None:
        print("Traces cannot be aligned")
        return None

    fig, ax = plt.subplots()
    ax.plot(samples_valid, label=path_static)
    ax.plot(range(offset_invalid_x, len(samples_invalid) + offset_invalid_x), samples_invalid,
            label=path_shift)

    plt.xlabel("Sample number")
    plt.ylabel("Values")
    plt.show()

def main():
    parser = argparse.ArgumentParser(
        prog="TRS overlay",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument("--static", help="Path to trsfile which will be static", type=str, required=True)
    parser.add_argument("--shift", help="Path to trsfile which will be moved", type=str, required=True)
    parser.add_argument('--config', help="Extraction configuration file in toml format", required=True,
                                         type=str)

    args = parser.parse_args()
    config = ExtractionConfig.load_from_toml(args.config)
    trs_overlay(args.static, args.shift, config)


if __name__ == '__main__':
   main()