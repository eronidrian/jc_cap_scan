import threading
import time
import os
import ctypes

import numpy as np
from picosdk.ps4000 import ps4000 as ps
from picosdk.functions import adc2mV, assert_pico_ok, mV2adcpl1000
from trsfile import trs_open, Trace, SampleCoding, Header

from jc_cap_scan.config.config import CaptureConfig
from jc_cap_scan.utils.cap_file_utils import install, uninstall, call, reset_fault_counter, is_installation_successful

# Constants and configurations

# Manually define the constants if not available in the ps4000 module
PS4000_TRIGGER_AUX = 5  # Assuming 5 is the correct value for AUX based on the documentation
PS4000_RISING = 2  # Assuming 2 is the correct value for RISING based on the documentation
PS4000_MAX_VALUE = ctypes.c_int32(32_764)
PS4000_MAX_SAMPLES_PER_S = 80_000_000

VALID_CAP_FILE_PATH = "templates/good_package.cap"

def get_actual_sample_interval(target_sample_interval: float) -> float:
    timebase = ns_to_timebase(target_sample_interval)
    return timebase_to_ns(timebase)

def channel_range_to_str(channel_range: int) -> str | None:
    channel_range_map = {
        10: "PS4000A_10MV",
        20: "PS4000_20MV",
        50: "PS4000_50MV",
        100: "PS4000_100MV",
        200: "PS4000_200MV",
        500: "PS4000_500MV",
        1000: "PS4000_1V",
        2000: "PS4000_2V",
        5000: "PS4000_5V",
        10_000: "PS4000_10V",
        20_000: "PS4000_20V",
        50_000: "PS4000_50V",
    }
    range_str = channel_range_map.get(channel_range)
    if range_str is None:
        raise ValueError(f"Channel range {channel_range} is not supported by Piscoscope")
    return range_str

def timebase_to_ns(timebase: int) -> float | ValueError:
    if 0 <= timebase <= 2:
        return 2 ** timebase / PS4000_MAX_SAMPLES_PER_S * 10**9
    if 3 <= timebase <= 2**30 - 1:
        return (timebase - 1) / (PS4000_MAX_SAMPLES_PER_S - 60_000_000) * 10**9
    raise ValueError(f"Invalid timebase {timebase}")


# picoscope 4000 programmer guide page 13
def ns_to_timebase(ns: float) -> int:
    if 0 < ns < 18.75:
        return 0
    if 18.75 <= ns < 37.5:
        return 1
    if 37.5 <= ns < 75:
        return 2
    if 75 <= ns <= 54 * 10**9:
        return round((PS4000_MAX_SAMPLES_PER_S - 60_000_000) * ns / 10 ** 9) + 1

    raise ValueError(f"Invalid nanoseconds {ns}")


# PicoScope setup and capture functions
def setup_picoscope(capture_config: CaptureConfig):
    chandle = ctypes.c_int16()
    status = {}

    status["openunit"] = ps.ps4000OpenUnit(ctypes.byref(chandle), None)
    assert_pico_ok(status["openunit"])

    chARange = ps.PS4000_RANGE[channel_range_to_str(capture_config.channel_range)]
    status["setChA"] = ps.ps4000SetChannel(chandle, 0, 1, 1, chARange)
    assert_pico_ok(status["setChA"])

    chBRange = ps.PS4000_RANGE[channel_range_to_str(1000)]
    status["setChB"] = ps.ps4000SetChannel(chandle, 1, 1, 1, chBRange)
    assert_pico_ok(status["setChB"])

    # Set up single trigger on AUX IN
    status["trigger"] = ps.ps4000SetSimpleTrigger(chandle, 1, 1, mV2adcpl1000(capture_config.trigger_threshold, 1000, PS4000_MAX_VALUE), PS4000_RISING, capture_config.posttrigger_delay,
                                                  capture_config.autotrigger)
    assert_pico_ok(status["trigger"])

    return chandle, status


def capture_trace(chandle, status: dict, trs_writer, capture_done_event, number_of_samples: int, sample_interval: float):
    try:
        # Set number of pre and post trigger samples to be collected
        preTriggerSamples = 10
        postTriggerSamples = number_of_samples  # 25 million samples
        maxSamples = preTriggerSamples + postTriggerSamples

        # Set up buffers
        bufferBMax = (ctypes.c_int16 * maxSamples)()
        bufferBMin = (ctypes.c_int16 * maxSamples)()

        # Set data buffer location for data collection from channel B
        status["setDataBuffersA"] = ps.ps4000SetDataBuffers(chandle, 0, ctypes.byref(bufferBMax),
                                                            ctypes.byref(bufferBMin), maxSamples, 0)
        assert_pico_ok(status["setDataBuffersA"])

        # Run block capture
        timebase = ns_to_timebase(sample_interval)
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()
        status["getTimebase2"] = ps.ps4000GetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), 1,
                                                       ctypes.byref(returnedMaxSamples), 0)
        assert_pico_ok(status["getTimebase2"])

        status["runBlock"] = ps.ps4000RunBlock(chandle, preTriggerSamples, postTriggerSamples, timebase, 0, None, 0,
                                               None, None)
        assert_pico_ok(status["runBlock"])

        # Check for data collection to finish
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            status["isReady"] = ps.ps4000IsReady(chandle, ctypes.byref(ready))

        # Retrieve data from scope
        overflow = ctypes.c_int16()
        cmaxSamples = ctypes.c_int32(maxSamples)
        status["getValues"] = ps.ps4000GetValues(chandle, 0, ctypes.byref(cmaxSamples), 1, 0, 0, ctypes.byref(overflow))
        assert_pico_ok(status["getValues"])

        # Convert ADC counts data to mV
        maxADC = ctypes.c_int16(32512)
        chBRange = 5  # Make sure this matches the range set in setup_picoscope
        adc2mVChBMax = adc2mV(bufferBMax, chBRange, maxADC)

            # Save trace data to .trs file
        if trs_writer is not None:
            max_value = np.max(np.abs(adc2mVChBMax))
            adc2mVChBMax_byte = np.clip((adc2mVChBMax / (max_value / 127.0)), -128, 127).astype(np.int8)

            trs_writer.extend([Trace(SampleCoding.BYTE, adc2mVChBMax_byte)])

    finally:
        capture_done_event.set()



def run_installation_capture(chandle, status: dict, trs_writer, cap_file_name: str,  number_of_samples: int, sample_interval: float, auth: list[str] | None = None) -> tuple[bool, str]:
    capture_done_event = threading.Event()

    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_trace,
                                      args=(chandle, status, trs_writer, capture_done_event,  number_of_samples, sample_interval))
    capture_thread.start()

    # Wait a short time to ensure capture has started
    time.sleep(0.1)

    # Perform installation (this is what we want to capture)
    success, result = is_installation_successful(cap_file_name, auth)

    # Wait for capture to complete
    capture_done_event.wait()

    return success, result


def run_call_capture(chandle, status: dict, trs_writer, cap_name: str, number_of_samples: int, sample_interval: float, auth: list[str] | None):
    capture_done_event = threading.Event()

    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_trace,
                                      args=(chandle, status, trs_writer, capture_done_event,  number_of_samples, sample_interval))
    capture_thread.start()

    # Wait a short time to ensure capture has started
    time.sleep(0.1)

    # Perform installation (this is what we want to capture)
    call(False, auth)

    # Wait for capture to complete
    capture_done_event.wait()


def setup(capture_config: CaptureConfig):
    chandle, status = setup_picoscope(capture_config)

    # Define the trace parameter definitions and header for the trs file

    header = {
        Header.TRS_VERSION: 2,
        Header.SCALE_X: 1e-6,
        Header.SCALE_Y: 1e-3,
        Header.DESCRIPTION: 'PicoScope Full Data',
        Header.NUMBER_SAMPLES: capture_config.number_of_samples + 10,  # Pre-trigger + post-trigger samples
        Header.SAMPLE_CODING: SampleCoding.BYTE,
        Header.TRACE_TITLE: 'PicoScope Data',
    }

    return chandle, status, header


def capture_call_trace(cap_file_name: str, num_of_traces: int, result_folder: str, capture_config: CaptureConfig, auth: list[str] | None = None):
    chandle, status, header = setup(capture_config)
    install(cap_file_name, auth)

    try:
        run_call_capture(chandle, status, None, cap_file_name, capture_config.number_of_samples, capture_config.sample_interval, auth)
        trs_file_path = os.path.join(result_folder, f"traces_{cap_file_name}.trs")
        with trs_open(trs_file_path, 'w', headers=header) as trs_writer:
            for trace_num in range(num_of_traces):
                print(f"Trace: {trace_num + 1}/{num_of_traces}")
                run_call_capture(chandle, status, trs_writer, cap_file_name, capture_config.number_of_samples, capture_config.sample_interval, auth)
    finally:
        uninstall(cap_file_name, auth)
        ps.ps4000Stop(chandle)
        ps.ps4000CloseUnit(chandle)


def capture_install_trace(cap_file_name: str, num_of_traces: int, trs_file_path: str, capture_config: CaptureConfig, auth: list[str] | None = None) -> tuple[bool, str]:
    chandle, status, header = setup(capture_config)

    try:
        reset_fault_counter(auth)
        with trs_open(trs_file_path, 'w', headers=header) as trs_writer:
            for trace_num in range(num_of_traces):
                print(f"Trace: {trace_num + 1}/{num_of_traces}")
                success, result = run_installation_capture(chandle, status, trs_writer, cap_file_name, capture_config.number_of_samples, capture_config.sample_interval, auth)
    finally:
        ps.ps4000Stop(chandle)
        ps.ps4000CloseUnit(chandle)
    return success, result
