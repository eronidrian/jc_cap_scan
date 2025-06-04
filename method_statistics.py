import requests
import re
from urllib.parse import unquote
import csv

DOCS_URL = "https://docs.oracle.com/en/java/javacard/3.1/jc_api_srvc/api_classic/"


def get_full_webpage(package_name: str, class_name: str) -> str:
    url_end = package_name.replace('.', '/') + "/" + class_name + ".html"
    response = requests.get(DOCS_URL + url_end)
    if response.status_code != 200:
        print("Couldn't load documentation")
        exit()
    return response.text


def find_method_parameters(webpage: str, method_name: str) -> list[str] | None:
    # print(webpage)
    match = re.search(fr'#{method_name}\((.*?)\)', webpage)
    if match:
        return unquote(match.group(1)).split(',')
    print(f"Method {method_name} not found")
    return None


def get_method_parameters(package_name: str, class_name: str, method_name: str) -> list[str] | None:
    webpage = get_full_webpage(package_name, class_name)
    return find_method_parameters(webpage, method_name)


def convert_parameters(parameters: list[str]) -> str:
    return f"({';'.join(parameters)})"

# parameters = get_method_parameters("javacard.framework", "PIN", "getTriesRemaining")

input_filename = "overview_table.csv"
output_filename = "method_statistics.csv"

with open(input_filename, "r") as f:
    csv_reader = csv.reader(f)
    entries = [row for row in csv_reader]

for entry in entries:
    if len(entry) == 6:
        parameters = get_method_parameters(entry[1], entry[3], entry[5])
        parameters = parameters if parameters is not None else 'ERROR'
        print(entry[1], entry[3], entry[5], parameters)
        entry.append(convert_parameters(parameters))

with open(output_filename, "w") as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(["AID", "package name", "class token", "class name", "method token", "method name", "method parameters"])
    for row in entries:
        csv_writer.writerow(row)

