import pandas as pd
import trsfile
from numpy import ndarray
import numpy as np
from sklearn.preprocessing import minmax_scale



def load_trs_file(trs_path: str, rescale: bool, trace_index: int = 0, start: int = 0, end: int = -1, discard_max_n: int = 5) -> ndarray:
    """
    Load TRS file into numpy array
    :param trs_path: Path to TRS file
    :param rescale: Whether to rescale the trace using minmax_scale
    :param trace_index: Index of the trace in the TRS file to load (0-indexed)
    :param start: Start at sample
    :param end: End at sample
    :param discard_max_n: Discard n highest samples in the trace before rescaling (to remove outliers)
    :return:
    """
    with trsfile.open(trs_path, 'r') as traces:
        trace = np.copy(traces[trace_index].samples[start:end])
    # trace[trace > 95] = np.mean(trace)
    # trace[trace < 9] = np.mean(trace)
    if rescale:
        # for _ in range(discard_max_n):
        #     trace[np.argmax(trace)] = np.mean(trace)
        trace = np.abs(trace)
        return minmax_scale(trace)
    return trace
