from statistics import median

import matplotlib.pyplot as plt
import csv
import numpy as np

# path_to_results = "/home/petr/Downloads/diplomka/new_results/nxp_jcop_242/precise_measurements/all.csv"
# sample_interval = 25.6 # ns
#
#
# data = []
# with open(path_to_results, "r") as f:
#     csv_reader = csv.reader(f)
#     for row in csv_reader:
#         data.append(row)
#
# data = data[1:]
# data = [row[1:] for row in data]
# data = [[int(entry) for entry in row] for row in data]
# data = [[entry * sample_interval / 10**6 for entry in row] for row in data]
#
# data_shorts = [data[0] +  data[1], data[2] +  data[3], data[4] + data[5], data[6]]
#
#
# fig = plt.figure()
# plt.style.use('ggplot')
# plt.boxplot(data_shorts, showfliers=False, tick_labels=["1", "2 + 3", "4 + 5", "6 + 7"])
# plt.xlabel("Changed byte")
# plt.ylabel("Time [ms]")
# plt.title(f"Merged, shorts, full")
# plt.show()

# fig, ax = plt.subplots()
# for row in data:
#     plt.plot(row, '.')
# ax.set_ybound(110, 125)
# plt.show()

path_to_results = "/home/petr/Downloads/diplomka/new_results/nxp_jcop_242/bruteforce_attempt/bruteforce_results_2_160_ff.csv"
sample_interval = 25.6 # ns


data = []
with open(path_to_results, "r") as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        data.append(row)

data = [row[2:] for row in data]
data = [[int(entry) for entry in row] for row in data]
med_data = [median(row) for row in data]

differences = []

for i, entry in enumerate(med_data):
    left = med_data[i - 1] if i != 0 else med_data[i + 1]
    right = med_data[i + 1] if i != len(med_data) - 1 else med_data[i - 1]

    difference = abs(entry - left) + abs(entry - right)
    differences.append(difference)

print()

# data = [[entry * sample_interval / 10**6 for entry in row] for row in data]

fig = plt.figure()
plt.style.use('ggplot')
plt.plot(differences)
plt.show()


