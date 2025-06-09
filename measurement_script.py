import threading
import time
import os
import ctypes
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime  # For generating the folder name
from smartleia import TriggerPoints
from picosdk.ps6000 import ps6000 as ps
from picosdk.functions import adc2mV, assert_pico_ok
from trsfile import trs_open, Trace, SampleCoding, Header
from trsfile.parametermap import TraceParameterMap, TraceParameterDefinitionMap
from trsfile.traceparameter import ParameterType, TraceParameterDefinition, IntegerArrayParameter
import subprocess

matplotlib.use('Agg')  # Use the non-interactive Agg backend

# Constants and configurations
NUM_TRACES = 1  # Number of traces to capture

# Manually define the constants if not available in the ps6000 module
PS6000_TRIGGER_AUX = 5  # Assuming 5 is the correct value for AUX based on the documentation
PS6000_RISING = 2  # Assuming 2 is the correct value for RISING based on the documentation

# Leia setup functions
# def setup_leia():
#     target = TargetController(0)
#     target.configure_smartcard(protocol_to_use=1, ETU_to_use=None, freq_to_use=None,
#                                negotiate_pts=True, negotiate_baudrate=True)
#     ATR = target.get_ATR()
#     print(f"\nUsing protocol T={ATR.T_protocol_curr} with frequency {ATR.f_max_curr / 1000} KHz")
#
#     target.set_trigger_strategy(1, point_list=[TriggerPoints.TRIG_PRE_SEND_APDU], delay=0)
#
#     # # Select applet
#     # aid = [0x55, 0x6E, 0x69, 0x74, 0x54, 0x65, 0x73, 0x74]
#     # select_apdu = APDU(cla=0x00, ins=0xA4, p1=0x04, p2=0x00, lc=len(aid), data=aid)
#     # resp = target.send_APDU(select_apdu)
#     # if resp.sw1 != 0x90 or resp.sw2 != 0x00:
#     #     raise Exception(f"Failed to select applet: SW={resp.sw1:02X}{resp.sw2:02X}")
#
#     return target


# PicoScope setup and capture functions
def setup_picoscope():
    chandle = ctypes.c_int16()
    status = {}

    status["openunit"] = ps.ps6000OpenUnit(ctypes.byref(chandle), None)
    assert_pico_ok(status["openunit"])

    # Set up channel B with -150 mV offset
    chBRange = 6 # PS6000_RANGE["PS6000_1V"]
    offset_b_mv = -0.150  # -150 mV in volts
    status["setChB"] = ps.ps6000SetChannel(chandle, 1, 1, 1, chBRange, offset_b_mv, 0)
    assert_pico_ok(status["setChB"])

    # Set up single trigger on AUX IN
    threshold_mv = 50
    threshold = int(threshold_mv / 1000 * 32512)
    status["trigger"] = ps.ps6000SetSimpleTrigger(chandle, 1, PS6000_TRIGGER_AUX, threshold, PS6000_RISING, 0, 1000)
    assert_pico_ok(status["trigger"])

    return chandle, status


def capture_trace(chandle, status, trs_writer, capture_done_event, changed_byte, index, save_to_trs=True, folder=""):
    try:
        # Set number of pre and post trigger samples to be collected
        preTriggerSamples = 10
        postTriggerSamples = 25000000  # 25 million samples
        maxSamples = preTriggerSamples + postTriggerSamples

        # Set up buffers
        bufferBMax = (ctypes.c_int16 * maxSamples)()
        bufferBMin = (ctypes.c_int16 * maxSamples)()

        # Set data buffer location for data collection from channel B
        status["setDataBuffersB"] = ps.ps6000SetDataBuffers(chandle, 1, ctypes.byref(bufferBMax),
                                                            ctypes.byref(bufferBMin), maxSamples, 0)
        assert_pico_ok(status["setDataBuffersB"])

        # Run block capture
        sample_interval_ns = 300
        timebase = int(sample_interval_ns / 10**9 * 156250000) + 4
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

        # # Create time data
        # time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value / 1e6, cmaxSamples.value)
        #
        # # Create and save the plot
        # plt.figure(figsize=(12, 8))
        # key_text = f"Key: {key.hex()}"
        # pt_text = f"Plaintext: {plaintext.hex()}"
        # plt.text(0.05, -0.1, key_text, transform=plt.gca().transAxes, fontsize=9, verticalalignment='top')
        # plt.text(0.05, -0.15, pt_text, transform=plt.gca().transAxes, fontsize=9, verticalalignment='top')
        # plt.plot(time, adc2mVChBMax, label='Channel B')
        # plt.ylim([-700, 700])
        # plt.xlabel('Time (ms)')
        # plt.ylabel('Voltage (mV)')
        # plt.title(f'PicoScope Data {index}')
        # plt.legend()
        # plt.tight_layout()
        # plt.savefig(os.path.join(folder, f'trace_{index}.png'), dpi=300, bbox_inches='tight')
        # plt.close()  # Close the plot to avoid displaying it

        if save_to_trs:
            # Save trace data to .trs file
            max_value = np.max(np.abs(adc2mVChBMax))
            adc2mVChBMax_byte = np.clip((adc2mVChBMax / (max_value / 127.0)), -128, 127).astype(np.int8)

            trace_parameters = TraceParameterMap({
                'CHANGED': IntegerArrayParameter([changed_byte])
            })
            trs_writer.extend([Trace(SampleCoding.BYTE, adc2mVChBMax_byte, trace_parameters)])

            print(f"Trace saved: index {index}")
    finally:
        capture_done_event.set()


def install_package(changed_byte, package_name, changed_byte_value):
    subprocess.run(["java", "-jar", "gp.jar", "--install", f"templates_{changed_byte_value}/test_{package_name}_{changed_byte}.cap"], stdout=subprocess.PIPE)


def run_installation_and_capture(chandle, status, trs_writer, changed_byte, index, save_to_trs=True, folder=""):
    capture_done_event = threading.Event()

    # Start capture in a separate thread
    capture_thread = threading.Thread(target=capture_trace,
                                      args=(chandle, status, trs_writer, capture_done_event, changed_byte, index, save_to_trs, folder))
    capture_thread.start()

    # Wait a short time to ensure capture has started
    time.sleep(0.1)

    # Perform installation (this is what we want to capture)
    package_name = "javacardx_crypto"
    changed_byte_value = "ff"
    install_package(changed_byte, package_name, changed_byte_value)

    # Wait for capture to complete
    capture_done_event.wait()

    subprocess.run(["java", "-jar", "gp.jar", "--uninstall",
                    f"templates_{changed_byte_value}/test_{package_name}_{changed_byte}.cap"], stdout=subprocess.PIPE)


def main():
    start_time = time.time()  # Start timing the program

    # Create a folder named with the current date and time
    folder_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(folder_name, exist_ok=True)
    print(f"Saving files to folder: {folder_name}")

    # target = setup_leia()
    chandle, status = setup_picoscope()

    print("Performing dummy capture...")
    changed_byte = 0
    run_installation_and_capture(chandle, status, None, changed_byte, "dummy", save_to_trs=False, folder=folder_name)

    # Remove dummy files
    dummy_png = os.path.join(folder_name, "trace_dummy.png")
    if os.path.exists(dummy_png):
        os.remove(dummy_png)
        print(f"Removed {dummy_png}")

    # Define the trace parameter definitions and header for the trs file
    trace_parameter_definitions = TraceParameterDefinitionMap({
        'CHANGED': TraceParameterDefinition(ParameterType.INT, 1, 0),
    })

    header = {
        Header.TRS_VERSION: 2,
        Header.SCALE_X: 1e-6,
        Header.SCALE_Y: 1e-3,
        Header.DESCRIPTION: 'PicoScope Full Data',
        Header.NUMBER_SAMPLES: 25000010,  # Pre-trigger + post-trigger samples
        Header.SAMPLE_CODING: SampleCoding.BYTE,
        Header.TRACE_TITLE: 'PicoScope Data',
        Header.TRACE_PARAMETER_DEFINITIONS: trace_parameter_definitions
    }

    trs_file_path = os.path.join(folder_name, "all_traces.trs")
    with trs_open(trs_file_path, 'w', headers=header) as trs_writer:
        try:
            for index in range(NUM_TRACES):
                print(f"Processing input {index + 1}/{NUM_TRACES}")
                run_installation_and_capture(chandle, status, trs_writer, changed_byte, index, folder=folder_name)
                print(f"Completed capture for input {index + 1}")
        finally:
            # Clean up
            # target.close()
            ps.ps6000Stop(chandle)
            ps.ps6000CloseUnit(chandle)

    end_time = time.time()  # End timing the program
    elapsed_time = end_time - start_time
    print(f"Total execution time: {elapsed_time:.2f} seconds")


if __name__ == "__main__":
    main()