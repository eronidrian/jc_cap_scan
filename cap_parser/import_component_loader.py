from os import path


def load_import_component(directory: str) -> list[str]:
    with open(path.join(directory, "Import.cap"), "rb") as f:
        import_component = f.read()

    count = import_component[3]
    packages = import_component[4:]

    start = 0
    aids = []
    for _ in range(count):
        minor_version = packages[start]
        major_version = packages[start + 1]
        aid_len = packages[start + 2]
        aid = packages[start + 3: start + 3 + aid_len].hex().upper()
        start = start + 3 + aid_len
        aids.append(aid.lower())
        # print(f"Minor version: {minor_version}")
        # print(f"Major version: {major_version}")
        # print(f"AID: {aid}")
        # print()
    return aids