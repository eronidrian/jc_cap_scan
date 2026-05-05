import trsfile
from numpy import ndarray
import numpy as np
from sklearn.preprocessing import minmax_scale



def load_trs_file(trs_path: str, rescale: bool, trace_index: int = 0, start: int = 0, end: int = -1, top: float | None = None, bottom: float | None = None) -> ndarray:
    """
    Load TRS file into numpy array
    :param trs_path: Path to TRS file
    :param rescale: Whether to rescale the trace using minmax_scale
    :param trace_index: Index of the trace in the TRS file to load (0-indexed)
    :param start: Start at sample
    :param end: End at sample
    :param top: Replace values larger than top by mean value. Used to remove outliers
    :param bottom: Replace values smaller than bottom by mean value. Used to remove outliers
    :return:
    """
    with trsfile.open(trs_path, 'r') as traces:
        trace = np.copy(traces[trace_index].samples[start:end])
    if top is not None:
        trace[trace > top] = np.mean(trace)
    if bottom is not None:
        trace[trace < bottom] = np.mean(trace)
    if rescale:
        trace = np.abs(trace)
        return minmax_scale(trace)
    return trace
