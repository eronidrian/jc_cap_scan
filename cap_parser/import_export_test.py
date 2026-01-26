import os

from cap_parser.cap_file import CapFile

def diff(string_1, string_2) -> None:
    for i in range(len(string_1)):
        if string_1[i] != string_2[i]:
            print(f"Difference at position: {i}")
            print(f"First string: {string_1[i - 5 : i + 5]}")
            print(f"Second string: {string_2[i - 5 : i + 5]}")
            break


for name, component in CapFile.components:
    print(name)
    cap_file = CapFile()
    try:
        component_imported = component.load_from_file(cap_file, os.path.join("..", "simple_applet", "applets", "javacard", component.filename))
    except Exception as e:
        print("Import failed")
        print(e)
        continue

    try:
        component_imported.export_to_file(os.path.join("..", component.filename))
    except Exception as e:
        print("Export failed")
        print(e)
        continue

    with open(f"../simple_applet/applets/javacard/{component.filename}", "rb") as f:
        old = f.read()

    with open(f"../{component.filename}", "rb") as f:
        new = f.read()

    if old != new:
        print("Exported file doesn't match the original file")
        print("Original:")
        print(old.hex())
        print("Exported:")
        print(new.hex())
        diff(old.hex(), new.hex())
    else:
        print("All tests passed.")