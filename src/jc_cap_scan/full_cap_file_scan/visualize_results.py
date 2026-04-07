import csv

import numpy as np
import pandas as pd
import trsfile
from matplotlib import pyplot as plt
import seaborn as sns

results = pd.read_csv("results_javacos_periods.csv", names=["component", "byte_number", "diff"])
# results = results[results['message'] != "CAP loaded"]
# print(results.to_string())

with trsfile.open("traces_javacos/base_install_resampled_2000.trs", 'r') as traces_valid:
    samples_valid = traces_valid[0].samples

results['byte_number'] += 50

fig, ax = plt.subplots()
ax.plot(samples_valid[:8_000_000])
sns.scatterplot(data = results, x="diff", y="byte_number", hue='component', palette='deep')
ax.legend(loc='upper right')
plt.show()

