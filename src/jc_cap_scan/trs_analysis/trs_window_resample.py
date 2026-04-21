# provided by Lukasz Chmielewski
import argparse

import trsfile
import numpy as np

from numpy.lib.stride_tricks import sliding_window_view


# window = 1000
# overlap = 0.99
# ABS = False
# # step = window - int(window * overlap) #1
# step = 1

def window_resample(window: int, overlap: float | None, abs: bool, step: int, input_trs_file: str, output_trs_file: str, trace_index: int = 0):
    """
    Process trace using average window resampling
    :param window: Length of the window to average
    :param overlap: Overlap of the windows
    :param abs: Whether to use absolute window resampling
    :param step: Step to move the window
    :param input_trs_file: Path to TRS file to resample
    :param output_trs_file: Path to TRS file to output the resampled trace
    :param trace_index: Index of trace from the input_trs_file to process (0-indexed)
    :return:
    """
    if overlap is not None:
        step = window - int(window * overlap)

    with trsfile.open(input_trs_file, 'r') as traces:
        scale_X = traces.get_headers().get(trsfile.Header.SCALE_X)
        scale_Y = traces.get_headers().get(trsfile.Header.SCALE_Y)

        with trsfile.trs_open(
            output_trs_file,
            'w',
            engine = 'TrsEngine',
            headers = {
                trsfile.Header.TRS_VERSION: 2,
                trsfile.Header.SCALE_X: scale_X,
                trsfile.Header.SCALE_Y: scale_Y,
                trsfile.Header.DESCRIPTION: 'Window Resampled Traces',
            },
            padding_mode = trsfile.TracePadding.AUTO,
            live_update = True
        ) as wrtraces:

            trace_array = traces[trace_index].samples

            sw = sliding_window_view(trace_array, window_shape=window)
            if step > 1:
                sw = sw[::step]
            if abs:
                sw = np.abs(sw)
            processed = sw.mean(axis=1)

            wrtraces.append(
                    trsfile.Trace(
                        trsfile.SampleCoding.FLOAT,
                        processed
                    )
                )

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="Window resample"
    )
    parser.add_argument("-w", "--window", help="Length of the window", required=True, type=int)
    parser.add_argument("--overlap", help="Overlap of the windows", required=False, type=float)
    parser.add_argument("--abs", help="Use absolute window resample", action="store_true", required=False)
    parser.add_argument("-s", "--step", help="Step size", required=True, type=int)
    parser.add_argument("-i", "--input", help="Path to input .trs file", required=True)
    parser.add_argument("-o", "--output", help="Path to output .trs file", required=True)
    parser.add_argument("-t", "--trace_index", help="Index of the trace from .trs file to process", required=False, default=0, type=int)

    args = parser.parse_args()

    window_resample(args.window, args.overlap, args.abs, args.step, args.input, args.output, args.trace_index)

