import threading
import time
import os
import ctypes

import numpy as np
from picosdk.ps6000 import ps6000 as ps
from picosdk.functions import adc2mV, assert_pico_ok
from trsfile import trs_open, Trace, SampleCoding, Header

from config import MeasurementConfig
from utils.cap_file_utils import install, uninstall, call, reset_fault_counter

# Constants and configurations

# Manually define the constants if not available in the ps6000 module
PS6000_TRIGGER_AUX = 5  # Assuming 5 is the correct value for AUX based on the documentation
PS6000_RISING = 2  # Assuming 2 is the correct value for RISING based on the documentation

VALID_CAP_FILE_PATH = "templates/good_package.cap"


def channel_range_to_str(channel_range: int) -> str | None:
    channel_range_map = {
        10: "PS6000A_10MV",
        20: "PS6000_20MV",
        50: "PS6000_50MV",
        100: "PS6000_100MV",
        200: "PS6000_200MV",
        500: "PS6000_500MV",
        1000: "PS6000_1V",
        2000: "PS6000_2V",
        5000: "PS6000_5V",
        10_000: "PS6000_10V",
        20_000: "PS6000_20V",
        50_000: "PS6000_50V",
    }
    range_str = channel_range_map.get(channel_range)
    if range_str is None:
        raise ValueError(f"Channel range {channel_range} is not supported by Piscoscope")
    return range_str

# PicoScope setup and capture functions
def setup_picoscope(trigger_threshold: int, posttrigger_delay: int, channel_range: int):
    chandle = ctypes.c_int16()
    status = {}

    status["openunit"] = ps.ps6000OpenUnit(ctypes.byref(chandle), None)
    assert_pico_ok(status["openunit"])

    chBRange = ps.PS6000_RANGE[channel_range_to_str(channel_range)]
    offset_b_mv = -0.150  # -150 mV in volts
    status["setChB"] = ps.ps6000SetChannel(chandle, 1, 1, 1, chBRange, offset_b_mv, 0)
    assert_pico_ok(status["setChB"])

    # Set up single trigger on AUX IN
    threshold = int(32512/channel_range * trigger_threshold)
    status["trigger"] = ps.ps6000SetSimpleTrigger(chandle, 1, PS6000_TRIGGER_AUX, threshold, PS6000_RISING, posttrigger_delay,
                                                  100)
    assert_pico_ok(status["trigger"])

    return chandle, status


def capture_trace(chandle, status, trs_writer, capture_done_event, number_of_samples, sample_interval):
    try:
        # Set number of pre and post trigger samples to be collected
        preTriggerSamples = 10
        postTriggerSamples = number_of_samples  # 25 million samples
        maxSamples = preTriggerSamples + postTriggerSamples

        # Set up buffers
        bufferBMax = (ctypes.c_int16 * maxSamples)()
        bufferBMin = (ctypes.c_int16 * maxSamples)()

        # Set data buffer location for data collection from channel B
        status["setDataBuffersB"] = ps.ps6000SetDataBuffers(chandle, 1, ctypes.byref(bufferBMax),
                                                            ctypes.byref(bufferBMin), maxSamples, 0)
        assert_pico_ok(status["setDataBuffersB"])

        # Run block capture
        timebase = round(sample_interval / 10 ** 9 * 156250000) + 4
        print(f"ACTUAL SAMPLE INTERVAL: {(timebase - 4) / 156250000 * 10 ** 9} ns")
        timeIntervalns = ctypes.c_float()
        returnedMaxSamples = ctypes.c_int32()
        status["getTimebase2"] = ps.ps6000GetTimebase2(chandle, timebase, maxSamples, ctypes.byref(timeIntervalns), 1,
                                                       ctypes.byref(returnedMaxSamples), 0)
        assert_pico_ok(status["getTimebase2"])

        status["runBlock"] = ps.ps6000RunBlock(chandle, preTriggerSamples, postTriggerSamples, timebase, 0, None, 0,
                                               None, None)
        assert_pico_ok(status["runBlock"])

        # Check for data collection to finish
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            status["isReady"] = ps.ps6000IsReady(chandle, ctypes.byref(ready))

        # Retrieve data from scope
        overflow = ctypes.c_int16()
        cmaxSamples = ctypes.c_int32(maxSamples)
        status["getValues"] = ps.ps6000GetValues(chandle, 0, ctypes.byref(cmaxSamples), 1, 0, 0, ctypes.byref(overflow))
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



def run_installation_capture(chandle, status, trs_writer, cap_file_name,  number_of_samples, sample_interval, auth):
    capture_done_event = threading.Event()

    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_trace,
                                      args=(chandle, status, trs_writer, capture_done_event,  number_of_samples, sample_interval))
    capture_thread.start()

    # Wait a short time to ensure capture has started
    time.sleep(0.1)

    # Perform installation (this is what we want to capture)
    install(cap_file_name, auth)

    # Wait for capture to complete
    capture_done_event.wait()


def run_call_capture(chandle, status, trs_writer, cap_file_name,  number_of_samples, sample_interval, auth):
    capture_done_event = threading.Event()

    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_trace,
                                      args=(chandle, status, trs_writer, capture_done_event,  number_of_samples, sample_interval))
    capture_thread.start()

    # Wait a short time to ensure capture has started
    time.sleep(0.1)

    # Perform installation (this is what we want to capture)
    call(auth)

    # Wait for capture to complete
    capture_done_event.wait()


def setup(trigger_threshold, posttrigger_delay, number_of_samples, channel_range):
    chandle, status = setup_picoscope(trigger_threshold, posttrigger_delay, channel_range)

    # Define the trace parameter definitions and header for the trs file

    header = {
        Header.TRS_VERSION: 2,
        Header.SCALE_X: 1e-6,
        Header.SCALE_Y: 1e-3,
        Header.DESCRIPTION: 'PicoScope Full Data',
        Header.NUMBER_SAMPLES: number_of_samples + 10,  # Pre-trigger + post-trigger samples
        Header.SAMPLE_CODING: SampleCoding.BYTE,
        Header.TRACE_TITLE: 'PicoScope Data',
    }

    return chandle, status, header


def measure_cap_file_call(cap_file_name: str, num_of_measurements: int, result_folder: str, config: MeasurementConfig, auth: list[str] | None = None):
    chandle, status, header = setup(config.trigger_threshold, config.posttrigger_delay, config.number_of_samples, config.channel_range)
    install(cap_file_name, auth)

    try:
        run_call_capture(chandle, status, None, cap_file_name, config.number_of_samples, config.sample_interval, auth)
        trs_file_path = os.path.join(result_folder, f"traces_{cap_file_name}.trs")
        with trs_open(trs_file_path, 'w', headers=header) as trs_writer:
            for measurement in range(num_of_measurements):
                print(f"Measurement: {measurement + 1}/{num_of_measurements}")
                run_call_capture(chandle, status, trs_writer, cap_file_name, config.number_of_samples, config.sample_interval, auth)
    finally:
        uninstall(cap_file_name, auth)
        ps.ps6000Stop(chandle)
        ps.ps6000CloseUnit(chandle)


def measure_cap_file_install(cap_file_name: str, num_of_measurements: int, trs_file_path: str, config: MeasurementConfig, auth: list[str] | None = None):
    chandle, status, header = setup(config.trigger_threshold, config.posttrigger_delay, config.number_of_samples, config.channel_range)

    try:
        reset_fault_counter(auth)
        run_installation_capture(chandle, status, None, cap_file_name, config.number_of_samples, config.sample_interval, auth)
        uninstall(cap_file_name, auth)
        with trs_open(trs_file_path, 'w', headers=header) as trs_writer:
            for measurement in range(num_of_measurements):
                print(f"Measurement: {measurement + 1}/{num_of_measurements}")
                run_installation_capture(chandle, status, trs_writer, cap_file_name, config.number_of_samples, config.sample_interval, auth)
                uninstall(cap_file_name, auth)
    finally:
        ps.ps6000Stop(chandle)
        ps.ps6000CloseUnit(chandle)
