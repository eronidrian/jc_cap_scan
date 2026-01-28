import csv


directory_name = f"/home/petr/Downloads/diplomka/aid_results/smartcafe_6/new_measurement/precise_measurements/"

result_file = open(directory_name + "all.csv", "w")
csv_writer = csv.writer(result_file)
csv_writer.writerow(["modification"] + [i for i in range(1, 401)])
row_names = [f"AID {i}. byte" for i in range(1, 8)]
row_names.extend([
    "Major version",
])

new_rows = [[row_name] for row_name in row_names]
for i in range(8):
    new_row = []
    for changed_byte in ["ee", "ff"]:
        for package_name in ["javacard_security", "javacardx_crypto"]:
            full_name = directory_name + f"{package_name}_{changed_byte}_extract.csv"
            with open(full_name) as f:
                csv_reader = csv.reader(f)
                rows = list(csv_reader)
                rows = [row for row in rows if row[0] != 'modification']
                try:
                    new_rows[i].extend(rows[i][1:])
                except IndexError:
                    continue

for row in new_rows:
    csv_writer.writerow(row)
