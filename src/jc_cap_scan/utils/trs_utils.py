import trsfile
from numpy import ndarray
import numpy as np
from sklearn.preprocessing import minmax_scale



def load_trs_file(trs_path: str, rescale: bool, trace_index: int = 0, start: int = 0, end: int = -1, discard_max_n: int = 5) -> ndarray:
    with trsfile.open(trs_path, 'r') as traces:
        trace = np.copy(traces[trace_index].samples[start:end])
    if rescale:
        for _ in range(discard_max_n):
            trace[np.argmax(trace)] = np.mean(trace)
        trace = np.abs(trace)
        return minmax_scale(trace)
    return trace

