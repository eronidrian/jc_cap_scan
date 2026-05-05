# from cap_parser.cap_file import CapFile
# from cap_parser.import_component import PackageInfo
# from utils.cap_file_utils import pack_directory_to_cap_file
# from utils.cap_manipulation_utils import generate_cap_for_package_aid
#
#
#
# cap_file = CapFile.load_from_directory("templates/generic_template/test/javacard")
# print(cap_file.import_component.packages[0])
# print(cap_file.import_component.packages[1])
# cap_file.import_component.packages.append(PackageInfo(cap_file, 0, 1, bytes.fromhex("A000000062FF01")))
# cap_file.export_to_directory("load_enumeration/import_A000000062FF01/test/javacard")
#
# # cap_file.header_component.package.aid = bytearray.f   romhex("ffff")
#
# # cap_file.export_to_directory("load_enumeration/header_component/test/javacard")
# # f = open("load_enumeration/staticfield_component/test/javacard/StaticField.cap", "rb")
# # content = bytearray(f.read())
# # content[2] = 0x00
# # f.close()
# # print(content.hex())
# #
# # fw = open("load_enumeration/staticfield_component/test/javacard/StaticField.cap", "wb")
# # fw.write(bytes(content))
# # fw.close()
# pack_directory_to_cap_file("load_enumeration/import_A000000062FF01.cap", "load_enumeration/import_A000000062FF01")
#
#
#
#
#
#
#
#
#
#
#
# # header magic not checked
# # directory custom components not checked
# import csv
#
# from config import Config
# from trs_analysis.trs_extractor import extract_times_from_trs_file
#
# config = Config.load_from_toml("javacos_a_40_config.toml")
# f = open("nxp_jcop_4.csv", "w")
# csv_writer = csv.writer(f)
#
# for byte_number in range(9):
#     aid = bytearray.fromhex("a00000006202080101")
#     aid[byte_number] = 255
#     filename = f"traces/test_{aid.hex()}.trs"
#     print(filename)
#     times = extract_times_from_trs_file(filename, config.extraction)
#     print(times)
#     csv_writer.writerow([byte_number + 1] + times)
import csv
import ctypes
import os

from joblib.numpy_pickle_compat import read_zfile
from picosdk.functions import mV2adcpl1000

from api_specification.api_specification import API_305_SPECIFICATION
from jc_cap_scan.config.config import Config
from jc_cap_scan.trs_analysis.trs_extractor import extract_all_times_from_trs_file
from jc_cap_scan.utils.stat_utils import data_to_one_column, normalize_by_buckets, limit_range


def process_load_scan():
    import csv
    import os

    import pandas as pd

    from jc_cap_scan.trs_analysis.trs_diff import get_diff_periods, get_diff
    from jc_cap_scan.config.config import Config

    component_names = [
        "Header",
        "Directory",
        "Applet",
        "Import",
        "ConstantPool",
        "Class",
        "Method",
        "StaticField",
        "RefLocation"
    ]

    f = open("results_jcop_4_periods.csv", "a")
    csv_writer = csv.writer(f)

    config = Config.load_from_toml("config/jcop_4_config.toml")

    for component in component_names:
        print(f"Testing {component} component")
        component_name = f"{component}.cap"
        component_path = os.path.join("templates", "generic_template", "test", "javacard", component_name)
        if not os.path.exists(component_path):
            print("Component does not exists in the template and will not be tested")
            continue
        component_length = os.path.getsize(component_path)
        traces_directory = "/home/petr/Downloads/diplomka/load_scan_results/traces_jcop_4"
        for byte_number in range(component_length):
            trace_path = os.path.join(traces_directory, f"{component}_{byte_number}_resampled.trs")
            print(f"Processing {trace_path}")
            if not os.path.exists(trace_path):
                continue
            first_diff = get_diff(os.path.join(traces_directory, "base_install_resampled.trs"),
                                          trace_path, 1.5, 0.6, 'periods', False, 6_700_000, config.extraction)
            print(first_diff)
            csv_writer.writerow([component, byte_number, first_diff])


def extract_old_measurements():
    import csv

    from jc_cap_scan.config.config import Config
    from jc_cap_scan.trs_analysis.trs_extractor import extract_single_time_from_trs_file, find_high_consumption_periods, \
        extract_all_times_from_trs_file
    from jc_cap_scan.utils.trs_utils import load_trs_file

    config = Config.load_from_toml("config/smartcafe_60_config.toml")

    f = open("results_class_smartcafe.csv", "w")
    csv_writer = csv.writer(f)

    for class_token in range(255):
        print(class_token)
        file = f"/home/petr/Downloads/diplomka/class_results/with_time/smartcafe/traces/class_A0000000620102_{class_token}.trs"
        if not os.path.exists(file):
            continue
        times = extract_all_times_from_trs_file(file, config.extraction)
        for item in times:
            csv_writer.writerow([class_token] + item)
#

def extract_class_scan():
    import csv

    from jc_cap_scan.config.config import Config, ExtractionConfig
    from jc_cap_scan.trs_analysis.trs_extractor import extract_single_time_from_trs_file

    config = Config.load_from_toml("config/jcop_4_config.toml")

    f = open("results.csv", "w")
    csv_writer = csv.writer(f)

    for class_token in range(0, 31):
        print("class_token:", class_token)
        trs_file = f"traces/class_A0000000620102_{class_token}.trs"
        times = extract_single_time_from_trs_file(trs_file, config.extraction)
        csv_writer.writerow([class_token] + times)


import pandas as pd



def process_old_measurements():
    import pandas as pd
    from matplotlib import pyplot as plt
    import seaborn as sns
    import matplotlib as mpl

    base_path = "/home/petr/Downloads/diplomka/aid_results/smartcafe_6/measurement_at_home"
    filename = base_path + "/results.csv"

    data = pd.read_csv(filename, names=list(range(66)), usecols=list(range(66)))
    data.dropna(thresh=20, inplace=True)
    # print(data.head())

    # data = data.map(lambda x: (x * 25.6) / 10 ** 6)
    data.info()

    # for i in range(50):
    # i = 24
    # print(i)

    # mpl.use("pgf")
    # mpl.rcParams.update({
    #     "pgf.texsystem": "pdflatex",
    #     'font.family': 'serif',
    #     'text.usetex': True,
    #     'pgf.rcfonts': False,
    #     # 'font.size': 1,
    #     "axes.titlesize": 20,
    #     "axes.labelsize": 15,
    #     "xtick.labelsize": 15,
    #     "ytick.labelsize": 15,
    #     "legend.fontsize": 15,
    #     "figure.titlesize": 25,
    # })

    fig, ax = plt.subplots()

    print(data.head())
    subset = data.iloc[:, [1, 4]].transpose()
    # print(subset.head())
    s = pd.Series(subset.iloc[1].values, index=subset.iloc[0].values)
    groups = s.groupby(level=0, sort=False)
    cols = [pd.Series(vals.tolist(), name=hdr) for hdr, vals in groups]
    result = pd.concat(cols, axis=1)
    result = result.map(lambda x: (x * 50.2) / 10 ** 6)
    # print(result.head())
    # result = result.iloc[:, :8]
    print(result.to_string())
    # result.dropna(inplace=True)
    # print(result.to_string())

    # result = normalize_by_buckets(result, [(3.75, 3.79), (3.791,3.83)])
    # result = data_to_one_column(result)
    # result = limit_range(result, 3.5, 4)

    # medians = result.median(axis=0)
    # sns.scatterplot(medians)

    # ax.hist(result, bins=50)
    sns.boxplot(result, showfliers=False)
    # ax.hist(data[data < 10])
    ax.set_title("Javacos A40, class\_scan.3")
    ax.set_xlabel("Class token")
    ax.set_ylabel("LOAD period duration median [ms]")
    # plt.savefig(f"{base_path}/{i}.png")
    # plt.close()
    # fig.tight_layout()
    # fig.set_size_inches(w=5.00098, h=3.6)
    # plt.savefig("javacos_a_40_class_scan_3.pgf", bbox_inches='tight')
    # plt.show()
    # break

def extract_aid_list():
    config = Config.load_from_toml("config/jcop_4_config.toml")
    directory = "/home/petr/Downloads/diplomka/aid_list_results/nxp_jcop_4/traces"
    f = open("results_aid_list_jcop_4.csv", "w")
    csv_writer = csv.writer(f)
    for file in os.listdir(directory):
        print(file)
        name = file.split(".")[0]
        package_name = ".".join(name.split("_")[0:-2])
        package = API_305_SPECIFICATION.get_package_by_name(package_name)
        if package is not None:
            aid = package.aid
        else:
            print("AID not found")
            aid = "a00000015100"

        major = name.split("_")[2]
        minor = name.split("_")[3]
        times = extract_all_times_from_trs_file(os.path.join(directory, file), config.extraction)
        for item in times:
            csv_writer.writerow([aid, major, minor] + item)

def process_aid_list():
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt

    base_path = "/home/petr/Downloads/diplomka/aid_list_results/nxp_jcop_4"
    filename = base_path + "/results.csv"

    data = pd.read_csv(filename, names=list(range(48)), usecols=list(range(48)), index_col=[0,1,2])
    data = data.transpose()
    versions = [f"...{column[0][8:]}: v{column[1]}.{column[2]}" for column in data.columns]
    data.columns = versions
    # for i in range(40):
    i = 22
    print(i)
    subset = data.iloc[[i], :]
    s = pd.Series(subset.iloc[0].values, index=subset.columns)
    groups = s.groupby(level=0, sort=False)
    cols = [pd.Series(vals.tolist(), name=hdr) for hdr, vals in groups]
    result = pd.concat(cols, axis=1)

    result.to_csv("results_aid_list_jcop_4.csv")

    result = result.map(lambda x: (x * 50.2) / 10 ** 6)


    meds = result.median()
    print(meds)
    meds.sort_values(ascending=True, inplace=True)
    result = result[meds.index]
    # print(result.head())
    fig, ax = plt.subplots()

    sns.scatterplot(meds)
    # sns.boxplot(result, showfliers=False)
    # ax.hist(data[data < 10])
    ax.set_xlabel("Changed byte")
    ax.set_ylabel("Duration [ms]")
    plt.xticks(rotation=45, ha="right")
    # plt.savefig(f"{base_path}/{i}.png", bbox_inches='tight')
    # plt.close()
    plt.show()
    # print(data.head())


# process_old_measurements()
# process_aid_list()

f = open("/home/petr/Downloads/diplomka/aid_list_results/nxp_jcop_4/results.csv", "r")
csv_reader = csv.reader(f)

result = []
for line in csv_reader:
    aid = line[0]
    major = line[1]
    minor = line[2]
    if len(line) < 26:
        data = 0
    else:
        data = line[25]
    if not result:
        result.append([aid, major, minor, data])
        continue
    found = False
    for item in result:
        if item[0] == aid and item[1] == major and item[2] == minor:
            found = True
            item.append(data)
    if not found:
        result.append([aid, major, minor, data])

f.close()
f = open("results_aid_list_jcop_4.csv", "w")
csv_writer = csv.writer(f)
for item in result:
    csv_writer.writerow(item)
