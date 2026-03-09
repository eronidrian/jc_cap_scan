# provided by Lukasz Chmielewski
import argparse

import trsfile
import numpy as np
import math

# window = 1000
# overlap = 0.99
# ABS = False
# # step = window - int(window * overlap) #1
# step = 1

def window_resample(window: int, overlap: float | None, abs: bool, step: int, input_trs_file: str, output_trs_file: str, trace_index: int = 0):

    if overlap is not None:
        step = window - int(window * overlap)

    with trsfile.open(input_trs_file, 'r') as traces:
        scale_X = traces.get_headers().get(trsfile.Header.SCALE_X)
        scale_Y = traces.get_headers().get(trsfile.Header.SCALE_Y)
        lengthSamples = traces.get_headers().get(trsfile.Header.NUMBER_SAMPLES)

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

            for i, trace in enumerate(traces[trace_index]):
                trace_array = trace.samples
                length = math.ceil(lengthSamples / step)
                processed = np.zeros(length,float)

                for j in range(length):
                    start = j*step
                    if abs:
                        chunk = np.abs(trace_array[start:(start+window)])
                    else:
                        chunk = trace_array[start:(start+window)]
                    processed[j]= np.sum(chunk)/len(chunk)

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
    parser.add_argument("-w", "--window", help="Length of the window", required=True)
    parser.add_argument("--overlap", help="Overlap of the windows", required=False)
    parser.add_argument("--abs", help="Use absolute window resample", action="store_true", required=False)
    parser.add_argument("-s", "--step", help="Step size", required=True)
    parser.add_argument("-i", "--input", help="Path to input .trs file", required=True)
    parser.add_argument("-o", "--output", help="Path to output .trs file", required=True)
    parser.add_argument("-t", "--trace_index", help="Index of the trace from .trs file to process", required=False, default=0)

    args = parser.parse_args()

    window_resample(args.window, args.overlap, args.abs, args.step, args.input, args.output, args.trace_index)

