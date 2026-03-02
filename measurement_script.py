import threading
import time
import os
import ctypes
import numpy as np
from picosdk.ps6000 import ps6000 as ps
from picosdk.functions import adc2mV, assert_pico_ok
from trsfile import trs_open, Trace, SampleCoding, Header
import subprocess

# Constants and configurations

# Manually define the constants if not available in the ps6000 module
PS6000_TRIGGER_AUX = 5  # Assuming 5 is the correct value for AUX based on the documentation
PS6000_RISING = 2  # Assuming 2 is the correct value for RISING based on the documentation

# install setup
# THRESHOLD = 1  # mv
# SAMPLE_INTERVAL = 25  # ns
# NUMBER_OF_SAMPLES = 25 * 10 ** 6
# POSTTRIGGER_DELAY = 2900  # ms
# RANGE = 6

# call setup
THRESHOLD = 1  # mv
SAMPLE_INTERVAL = 10
NUMBER_OF_SAMPLES = 250_000
POSTTRIGGER_DELAY = 15 * 10 ** 6
RANGE = 5

VALID_CAP_FILE_PATH = "good_package.cap"
auth = []


# PicoScope setup and capture functions
def setup_picoscope():
    chandle = ctypes.c_int16()
    status = {}

    status["openunit"] = ps.ps6000OpenUnit(ctypes.byref(chandle), None)
    assert_pico_ok(status["openunit"])

    # Set up channel B with -150 mV offset
    chBRange = RANGE  # PS6000_RANGE["PS6000_1V"]
    offset_b_mv = -0.150  # -150 mV in volts
    status["setChB"] = ps.ps6000SetChannel(chandle, 1, 1, 1, chBRange, offset_b_mv, 0)
    assert_pico_ok(status["setChB"])

    # Set up single trigger on AUX IN
    threshold = int(THRESHOLD / 1000 * 32512)
    status["trigger"] = ps.ps6000SetSimpleTrigger(chandle, 1, PS6000_TRIGGER_AUX, threshold, PS6000_RISING, 0,
                                                  POSTTRIGGER_DELAY)
    assert_pico_ok(status["trigger"])

    return chandle, status


def capture_trace(chandle, status, trs_writer, capture_done_event, index, save_to_trs=True, folder=""):
    try:
        # Set number of pre and post trigger samples to be collected
        preTriggerSamples = 10
        postTriggerSamples = NUMBER_OF_SAMPLES  # 25 million samples
        maxSamples = preTriggerSamples + postTriggerSamples

        # Set up buffers
        bufferBMax = (ctypes.c_int16 * maxSamples)()
        bufferBMin = (ctypes.c_int16 * maxSamples)()

        # Set data buffer location for data collection from channel B
        status["setDataBuffersB"] = ps.ps6000SetDataBuffers(chandle, 1, ctypes.byref(bufferBMax),
                                                            ctypes.byref(bufferBMin), maxSamples, 0)
        assert_pico_ok(status["setDataBuffersB"])

        # Run block capture
        timebase = round(SAMPLE_INTERVAL / 10 ** 9 * 156250000) + 4
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

        if save_to_trs:
            # Save trace data to .trs file
            max_value = np.max(np.abs(adc2mVChBMax))
            adc2mVChBMax_byte = np.clip((adc2mVChBMax / (max_value / 127.0)), -128, 127).astype(np.int8)

            trs_writer.extend([Trace(SampleCoding.BYTE, adc2mVChBMax_byte)])

    finally:
        capture_done_event.set()


def install_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--install",
                           cap_file_name],
                          stdout=subprocess.PIPE)


def uninstall_package(cap_file_name):
    return subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                           cap_file_name],
                          stdout=subprocess.PIPE)


def reset_fault_counter():
    result = install_package(VALID_CAP_FILE_PATH)

    result = result.stdout.decode("utf-8")
    if result.find("CAP loaded") == -1:
        print("CARD UNRESPONSIVE! ABORTING!")
        exit(1)

    uninstall_package(VALID_CAP_FILE_PATH)


def call_package():
    command_apdu = "1234000000"
    return subprocess.run(["java", "-jar", "gp.jar", "--apdu",
                           "00A404000C73696D706C656170706C657400", "--apdu", command_apdu,
                           "-d"] + auth,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def run_installation_capture(chandle, status, trs_writer, cap_file_name, index,
                             save_to_trs=True, folder=""):
    capture_done_event = threading.Event()

    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_trace,
                                      args=(chandle, status, trs_writer, capture_done_event, index,
                                            save_to_trs, folder))
    capture_thread.start()

    # Wait a short time to ensure capture has started
    time.sleep(0.1)

    # Perform installation (this is what we want to capture)
    install_package(cap_file_name)

    # Wait for capture to complete
    capture_done_event.wait()


def run_call_capture(chandle, status, trs_writer, cap_file_name, index,
                     save_to_trs=True, folder=""):
    capture_done_event = threading.Event()

    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_trace,
                                      args=(chandle, status, trs_writer, capture_done_event, index,
                                            save_to_trs, folder))
    capture_thread.start()

    # Wait a short time to ensure capture has started
    time.sleep(0.1)

    # Perform installation (this is what we want to capture)
    call_package()

    # Wait for capture to complete
    capture_done_event.wait()


def setup():
    chandle, status = setup_picoscope()

    # Define the trace parameter definitions and header for the trs file

    header = {
        Header.TRS_VERSION: 2,
        Header.SCALE_X: 1e-6,
        Header.SCALE_Y: 1e-3,
        Header.DESCRIPTION: 'PicoScope Full Data',
        Header.NUMBER_SAMPLES: NUMBER_OF_SAMPLES + 10,  # Pre-trigger + post-trigger samples
        Header.SAMPLE_CODING: SampleCoding.BYTE,
        Header.TRACE_TITLE: 'PicoScope Data',
    }

    return chandle, status, header


def measure_cap_file_call(cap_file_name: str, num_of_measurements: int, result_folder: str):
    chandle, status, header = setup()
    install_package(cap_file_name)

    try:
        run_call_capture(chandle, status, None, cap_file_name, "dummy", save_to_trs=False, folder=result_folder)
        trs_file_path = os.path.join(result_folder, f"traces_{cap_file_name}.trs")
        with trs_open(trs_file_path, 'w', headers=header) as trs_writer:
            for measurement in range(num_of_measurements):
                print(f"Measurement: {measurement + 1}/{num_of_measurements}")
                run_call_capture(chandle, status, trs_writer, cap_file_name, measurement, folder=result_folder)
    finally:
        uninstall_package(cap_file_name)
        ps.ps6000Stop(chandle)
        ps.ps6000CloseUnit(chandle)


def measure_cap_file_install(cap_file_name: str, num_of_measurements: int, result_folder: str):
    chandle, status, header = setup()

    try:
        reset_fault_counter()
        run_installation_capture(chandle, status, None, cap_file_name,
                                 "dummy", save_to_trs=False, folder=result_folder)
        uninstall_package(cap_file_name)
        trs_file_path = os.path.join(result_folder, f"traces_{cap_file_name}.trs")
        with trs_open(trs_file_path, 'w', headers=header) as trs_writer:
            for measurement in range(num_of_measurements):
                print(f"Measurement: {measurement + 1}/{num_of_measurements}")
                run_installation_capture(chandle, status, trs_writer, cap_file_name, measurement, folder=result_folder)
                uninstall_package(cap_file_name)
    finally:
        ps.ps6000Stop(chandle)
        ps.ps6000CloseUnit(chandle)
