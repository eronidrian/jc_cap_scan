# provided by Lukasz Chmielewski
import argparse

import trsfile
from trsfile.parametermap import TraceSetParameterMap
import matplotlib.pyplot as plt
import sys


def visualize_trace(trace_path: str, trace_index: int):

    zoomS=0
    zoomE=-1
    start = trace_index
    number = 1
    displayLabels = 4
    displayData = True
    dataStart=0
    dataEnd=8
    repeat = 1
    together = False

    with trsfile.open(trace_path, 'r') as traces:
        if together:
            fig, ax = plt.subplots(repeat, sharex=True, sharey=True)
        else:
            fig = plt.figure()

        for r in range(repeat):
            #print(start+(r*number))
            #print(start+(r*number)+number-1)
            for i, trace in enumerate(traces[(start+(r*number)):(start+(r*number)+number)]):
                if i<number:
                    samples = trace.samples
                    if i < displayLabels:
                        if displayData:
                            if not together:
                                plt.plot(samples[zoomS:zoomE])
                            else:
                                #ax[i].set_title("Trace " + str(start+(r*number)+i))
                                ax[r].plot(samples[zoomS:zoomE])
                        else:
                            if not together:
                                plt.plot(samples[zoomS:zoomE])
                            else:
                                #ax[i].set_title("Trace " + str(start+(r*number)+i))
                                ax[r].plot(samples[zoomS:zoomE])
                    elif i == displayLabels:
                        if not together:
                            plt.plot(samples[zoomS:zoomE])
                        else:
                            #ax[i].set_title("Trace" + str(start+(r*number)+i))
                            ax[r].plot(samples[zoomS:zoomE])
                    else:
                        if not together:
                            plt.plot(samples[zoomS:zoomE])
                        else:
                            #ax[i].set_title("Trace" + str(start+(r*number)+i))
                            ax[r].plot(samples[zoomS:zoomE])
                else:
                    break
            if not together:
                plt.xlabel("Time")
                plt.ylabel("Values")
                plt.title("Traces ("+str(start+(r*number))+"-"+str(number+(r*number))+")")
                # plt.legend()
                plt.show()
            else:
                if i > 1:
                    ax[r].set_title("Traces ("+str(start+(r*number))+"-"+str(start+(r*number)+number-1)+")")
                    # ax[r].legend()
                else:
                    ax[r].set_title("Trace "+str(start+(r*number)))
                    # if displayData:
                        # ax[r].legend()
        if together:
            plt.xlabel("Time")
            #plt.ylabel("Values")
            fig.text(0.04, 0.5, "Values", va='center', rotation='vertical')
            fig.suptitle("Traces ("+str(start)+"-"+str(number+((r-1)*number))+")")
            #plt.title("Traces ("+str(start+(r*number))+"-"+str(number+(r*number))+")")
            #plt.legend()
            plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog="TRS visualizer"
    )
    parser.add_argument("-f", "--trs_file", help="Path to .trs file", required=True)
    parser.add_argument("-i", "--trace_index", help="Index of trace to visualize. Default 0", required=False, default=0)
    args = parser.parse_args()
    visualize_trace(args.trs_file, args.trace_index)