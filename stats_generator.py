import matplotlib.pyplot as plt
import csv
import numpy as np

path_to_results = "/home/petr/Downloads/diplomka/new_results/javacos_a_40/10_measurements_short_export/all.csv"
sample_interval = 25.6 # ns


data = []
with open(path_to_results, "r") as f:
    csv_reader = csv.reader(f)
    for row in csv_reader:
        data.append(row)

data = data[1:]
data = [row[1:] for row in data]
data = [[int(entry) for entry in row] for row in data]
data = [[entry * sample_interval / 10**6 for entry in row] for row in data]
data = data[:-2]
# print(data[1:][0][1:])

fig = plt.figure()
plt.boxplot(data, showfliers=False, tick_labels=[str(i) for i in range(1, 8)]) #+ ["major", "minor"])
plt.xlabel("Changed byte")
plt.ylabel("Time [ms]")
plt.style.use('ggplot')
plt.show()
