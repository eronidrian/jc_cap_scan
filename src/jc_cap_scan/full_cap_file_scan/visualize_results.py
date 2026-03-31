import csv

import pandas as pd
import trsfile
from matplotlib import pyplot as plt
import seaborn as sns

results = pd.read_csv("results.csv", names=["component", "byte_number", "message", "diff"])
results = results[results['message'] != "CAP loaded"]
# print(results.to_string())

with trsfile.open("traces/base_install_resampled.trs", 'r') as traces_valid:
    samples_valid = traces_valid[0].samples

results['byte_number'] += 41

fig, ax = plt.subplots()
ax.plot(samples_valid[:8_000_000])
sns.scatterplot(data = results, x="diff", y="byte_number", hue='component', palette='deep')
plt.show()

