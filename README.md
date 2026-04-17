# jc_cap_scan

`jc_cap_scan` is a tool for evaluating side channel leakage during an installation on an applet onto a Java Card. It also allows brute forcing parts of unknown API present on the Java Card. Moreover, this repository includes some utilities for general CAP file parsing and manipulation and power trace analysis. 

## Installation


## Typical workflow

The tool is not fully automatic because there are many variables in the process. The typical workflow for modules requiring power trace capture would be:
1. Tweak `capture` settings in the config using `capture_setup` such that the power trace's part of interest is properly captured.
2. Tweak `extraction` settings in the config using `extraction_setup` such that edges of regions in the trace are properly detected.
3. Run `full_cap_file_scan` to identify, which regions of the power trace correspond to which CAP file components. Using this knowledge, you can reduce the part of the power trace you are extracting.
4. Run module of your choice and get the results in `.csv` file.


## Configuration file

Configuration file is in `toml` format a can include one or both of the following sections: `[capture]` and `[extraction]`.

```toml
[capture]
trigger_threshold = 1000 # in mV, after reaching what threshold should the capture start
autotrigger = 1000 # in ms, artificially trigger after N ms
posttrigger_delay = 0 # in ms, how long should the oscilloscope wait after receiving trigger for starting the capture
number_of_samples = 15_000_000 # how many samples to capture
sample_interval = 50 # in ns, interval between taking two samples
channel_range = 200 # in mV, range of the Y-axis of the power trace

[extraction]
max_gap = 500 # number of samples, max gap between two periods that is bridged to merge them into a single period, happens before discarding periods using `min_duration`
min_duration = 800 # number of samples, periods shorter than this threshold are discarded
threhold = 0.65 # treshold for detecting raising and falling edges for starts and ends of the periods, for min-max rescaled trace
index_to_extract = 24 # period number that is important for the measurement, starts at 0
```


## Modules

The tool is split into multiple modules based on the experiments from the paper. Each module is called with `$ python3 -m jc_cap_scan.<module_name> <parameter>`. Use the `--help` flag to see detailed usage.  
If the module has visualization script, it can be called by replacing the last part of `module_name` with `visualize_results`, such as `package_scan.visualize_results`.

| Experiment(s) | module_name                                  | visualization script |
|---------------|----------------------------------------------|----------------------|
| #1, #2        | package_scan.package_side_channel_discovery  | ✅                    |
| #3            | package_scan.package_bruteforce              | ✅                    |
| #4            | aid_list_scan.aid_list_scan                  | ✅                    |
| #5, #6        | class_scan.class_bruteforce                  | ❌                    |
| #8            | class_scan.class_side_channel_discovery      | ✅                    |
| #9, #10, #11  | method_scan.method_bruteforce                | ❌                    |
| #X            | full_cap_file_scan.full_cap_file_scan        | ✅                    |
| #0, #7        | package_scan.pc_timer_side_channel_discovery | ✅                    |
 | #Y           | field_scan.field_scan                        | ❌                    |


## Traces analysis utils

The tool contains various utilities for analysing traces. All are called as `$ python3 -m jc_cap_scan.trs_analysis.<tool_name>`. You can use `--help` flag to see the usage details.

- `trs_diff` - Align and subtract two traces.
- `trs_extractor` - Extract starts and ends of periods from a trace.
- `trs_overlay` - Overlay and display two or more traces.
- `trs_visualizer` - Display a trace.
- `trs_window_resample` - Process a trace using average window resampling.

## CAP parser




## JC API specification
