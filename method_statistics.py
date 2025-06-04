import requests
import re
from urllib.parse import unquote
import csv

DOCS_URL_31 = "https://docs.oracle.com/en/java/javacard/3.1/jc_api_srvc/api_classic/"
DOCS_URL_32 = "https://docs.oracle.com/en/java/javacard/3.2/jcapi/api_classic/"


def load_webpage(url: str) -> str:
    response = requests.get(url)
    if response.status_code != 200:
        print("Couldn't load documentation")
        exit()
    return response.text


def get_package_list() -> list[str]:
    webpage = load_webpage(DOCS_URL_32 + "index.html")

    match = re.findall(r'<a href="(.*?)/package-summary.html">', webpage)
    return list(set(match))


def get_class_list(package_name: str) -> list[str]:
    webpage = load_webpage(f"{DOCS_URL_32}/{package_name}/package-summary.html")

    match = re.findall(r'<a href="([^/]*?).html" title', webpage)
    return list(set(match))


def get_method_list(package_name: str, class_name: str) -> list[str] | None:
    webpage = load_webpage(f"{DOCS_URL_32}/{package_name}/{class_name}.html")

    match = re.findall(r'#([a-zA-Z]*?)\(.*?\)">', webpage)
    return list(set(match))


def get_method_signatures(package_name: str, class_name: str, method_name: str) -> list[str] | None:
    webpage = load_webpage(f"{DOCS_URL_32}/{package_name}/{class_name}.html")

    matches = re.findall(fr'#{method_name}(\(.*?\))', webpage)
    if not matches:
        return []

    signatures = []
    for match in matches:
        signature = unquote(match)
        signature = signature.replace(",", ";")
        signatures.append(signature)
    return list(set(signatures))


csv_file = open("overview_table_320_new.csv", "w")
csv_writer = csv.writer(csv_file)

csv_writer.writerow(["package name", "class name", "method name", "method signature"])

packages = get_package_list()
for package in packages:
    classes = get_class_list(package)
    if not classes:
        continue
    for class_name in classes:
        methods = get_method_list(package, class_name)
        if not methods:
            print(package, class_name)
            csv_writer.writerow([package.replace("/", "."), class_name])
            continue
        for method in methods:
            if method == 'equals':
                continue
            signatures = get_method_signatures(package, class_name, method)
            if not signatures:
                print(f"ERROR. Signature for method {method}, package {package}, class {class_name} not found")
                exit()
            for signature in signatures:
                print(package, class_name, method, signature)
                csv_writer.writerow([package.replace("/", "."), class_name, method, signature])
