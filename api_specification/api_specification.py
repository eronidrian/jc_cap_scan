from __future__ import annotations

import csv
import re
import textwrap
from enum import Enum


class JCAccessFlag(Enum):
    STATIC = 0
    VIRTUAL = 1
    PUBLIC = 2
    PRIVATE = 3
    ABSTRACT = 4
    FINAL = 5
    PROTECTED = 6
    INTERFACE = 7

    @staticmethod
    def from_string(type_string: str) -> list[JCAccessFlag]:
        access_flags = []
        for access_flag in JCAccessFlag:
            if access_flag.name.lower() in type_string:
                access_flags.append(access_flag)
        return access_flags

    @staticmethod
    def to_string(access_flags: list[JCAccessFlag]) -> str:
        result = []
        for access_flag in JCAccessFlag:
            if access_flag in access_flags:
                result.append(access_flag.name.lower())
        return " ".join(result)


class JCField:
    def __init__(self, name: str, token: int, access_flags: list[JCAccessFlag], jc_type: str, value: int):
        self.name = name
        self.token = token
        self.access_flags = access_flags
        self.jc_type = jc_type
        self.value = value

    @staticmethod
    def descriptor_to_jc_type(descriptor: str) -> str | Exception:
        jc_type = None
        jc_type = "byte" if descriptor == "B" else jc_type
        jc_type = "short" if descriptor == "S" else jc_type
        jc_type = "boolean" if descriptor == "Z" else jc_type
        jc_type = "int" if descriptor == "I" else jc_type
        if descriptor.startswith("L"):
            jc_type = descriptor[1:-1]
            descriptor = descriptor.replace("/",".")
        if jc_type is None:
            raise ValueError(f"descriptor {descriptor} cannot be converted to jc type")
        return jc_type

    @staticmethod
    def load_from_export_file(content: list[str], offset: int) -> tuple[int, JCField]:
        offset += 1
        token = None
        name = None
        access_flags = None
        value = None
        jc_type = None
        while offset < len(content):
            line = content[offset].strip()
            if "field_info" in line or "class_info" in line or "method_info" in line:
                break
            elif "token" in line:
                token = int(line.split("\t")[1])
            elif "name_index" in line and not "attribute_name_index" in line:
                name = line.split("//")[1].strip()
            elif "Descriptor_Index" in line:
                jc_type = JCField.descriptor_to_jc_type(line.split("//")[1].strip())
            elif "access_flags" in line:
                access_flags = JCAccessFlag.from_string(line)
            elif "constantvalue_index" in line:
                value = int(line.split("=")[1])

            offset += 1

        return offset, JCField(name, token, access_flags, jc_type, value)

    def __str__(self):
        result_string = ""
        result_string += f"Name: {self.name}\n"
        result_string += f"Token: {self.token}\n"
        result_string += f"Access flags: {JCAccessFlag.to_string(self.access_flags)}\n"
        result_string += f"Type: {self.jc_type}\n"
        result_string += f"Value: {self.value}\n"
        return result_string


class JCMethod:
    def __init__(self, access_flags: list[JCAccessFlag], token: int, name: str, signature: str):
        self.access_flags = access_flags
        self.token = token
        self.name = name
        self.signature = signature.lower()

    @staticmethod
    def descriptor_to_signature(descriptor: str) -> str:
        match = re.search(r"(\(.*\))(.*)", descriptor)
        signature = match.group(1)

        signature = re.sub(r'\[B', "byte[];", signature)
        signature = re.sub(r'\[S', "short[];", signature)
        signature = re.sub(r'\[Z', "boolean[];", signature)
        signature = re.sub(r'\[I', "int[];", signature)

        signature = re.sub(f'SS', "short;short;", signature)
        signature = re.sub(f'BB', "byte;byte;", signature)
        signature = re.sub(f'II', "int;int;", signature)
        signature = re.sub(f'([ISBZ;(])I', r'\1int;', signature)
        signature = re.sub(f'([ISBZ;(])S', r'\1short;', signature)
        signature = re.sub(r'([ISBZ;(])B', r'\1byte;', signature)
        signature = re.sub(r'([ISBZ;(])Z', r'\1boolean;', signature)

        signature = re.sub(r'\(L', "(", signature)
        signature = re.sub(r';L', ";", signature)
        signature = re.sub("/", ".", signature)

        signature = re.sub(r';\)', ")", signature)

        return_value = match.group(2)
        return_value = re.sub(r'\[B', "byte[]", return_value)
        return_value = re.sub(r'\[S', "short[]", return_value)
        return_value = re.sub(r'\[Z', "boolean[]", return_value)
        return_value = re.sub(r'\[I', "int[]", return_value)
        return_value = re.sub(r'\[L(.*);', r'\1[]', return_value)

        return_value = "byte" if return_value == "B" else return_value
        return_value = "short" if return_value == "S" else return_value
        return_value = "boolean" if return_value == "Z" else return_value
        return_value = "int" if return_value == "I" else return_value
        return_value = "void" if return_value == "V" else return_value
        return_value = re.sub(r'L(.*);', r'\1', return_value)

        return_value = re.sub("/", ".", return_value)

        return return_value + signature

    @staticmethod
    def load_from_export_file(content: list[str], offset: int) -> tuple[int, JCMethod]:
        offset += 1
        token = None
        name = None
        access_flags = None
        signature = None
        while offset < len(content):
            line = content[offset].strip()
            if "field_info" in line or "class_info" in line or "method_info" in line:
                break
            elif "token" in line:
                token = int(line.split("\t")[1].strip())
            elif "name_index" in line:
                name = line.split("//")[1].strip()
            elif "Descriptor_Index" in line:
                signature = JCMethod.descriptor_to_signature(line.split("//")[1].strip())
            elif "access_flags" in line:
                access_flags = JCAccessFlag.from_string(line)

            offset += 1

        return offset, JCMethod(access_flags, token, name, signature)

    def __str__(self):
        result_string = ""
        result_string += f"Name: {self.name}\n"
        result_string += f"Token: {self.token}\n"
        result_string += f"Access flags: {JCAccessFlag.to_string(self.access_flags)}\n"
        result_string += f"Signature: {self.signature}\n"
        return result_string


class JCClass:
    def __init__(self, token: int, name: str, access_flags: list[JCAccessFlag]):
        self.token = token
        self.name = name
        self.access_flags = access_flags
        self.methods: list[JCMethod] = []
        self.fields: list[JCField] = []

    @property
    def virtual_methods(self) -> list[JCMethod]:
        return [method for method in self.methods if JCAccessFlag.VIRTUAL in method.access_flags]

    @property
    def static_methods(self) -> list[JCMethod]:
        return [method for method in self.methods if JCAccessFlag.STATIC in method.access_flags]

    def get_method_by_token_and_access_flags(self, token: int, access_flags: list[JCAccessFlag]) -> JCMethod | None:
        for method in self.methods:
            if method.token == token and method.access_flags == access_flags:
                return method
        return None

    def add_method(self, method: JCMethod) -> Exception | None:
        found_method = self.get_method_by_token_and_access_flags(method.token, method.access_flags)
        if found_method is not None and found_method.signature == method.signature:
            raise KeyError(
                f"Method with token {method.token}, access flags {method.access_flags} and signature {method.signature} is already present in the list of methods")
        self.methods.append(method)

    def add_field(self, field: JCField) -> Exception | None:
        self.fields.append(field)

    @staticmethod
    def load_from_export_file(content: list[str], offset: int) -> tuple[int | JCClass]:
        name = content[offset].split("//")[1].strip().split("/")[-1]
        # parsing class_info
        token = None
        access_flags = None
        for i, line in enumerate(content[offset:]):
            line = line.strip()
            if "token" in line:
                token = int(line.split("\t")[1].strip())
            if "access_flags" in line:
                access_flags = JCAccessFlag.from_string(line)
                break

        if token is None or access_flags is None:
            raise ValueError("token or access flags not found in export file")
        jc_class = JCClass(token, name, access_flags)

        offset += 1
        # parsing methods and fields
        while offset < len(content):
            line = content[offset]
            if "class_info" in line:
                break
            elif "field_info" in line:
                offset, jc_field = JCField.load_from_export_file(content, offset)
                jc_class.add_field(jc_field)
            elif "method_info" in line:
                offset, jc_method = JCMethod.load_from_export_file(content, offset)
                jc_class.add_method(jc_method)
            else:
                offset += 1

        return offset, jc_class

    def __str__(self):
        result_string = ""
        result_string += f"Name: {self.name}\n"
        result_string += f"Token: {self.token}\n"
        result_string += f"Access flags: {JCAccessFlag.to_string(self.access_flags)}\n"
        result_string += "Methods:\n"
        for jc_method in self.methods:
            result_string += textwrap.indent(str(jc_method), "\t")
            result_string += "\n"
        result_string += "Fields:\n"
        for jc_field in self.fields:
            result_string += textwrap.indent(str(jc_field), "\t")
            result_string += "\n"
        result_string += "\n"
        return result_string


class JCPackage:
    def __init__(self, aid: str, name: str):
        self.aid = aid.lower()
        self.name = name
        self.classes: list[JCClass] = []

    def get_class_by_token(self, token: int) -> JCClass | None:
        for jc_class in self.classes:
            if jc_class.token == token:
                return jc_class
        return None

    def get_class_by_name(self, name: str) -> JCClass | None:
        for jc_class in self.classes:
            if jc_class.name == name:
                return jc_class
        return None

    def add_class(self, jc_class: JCClass) -> Exception | None:
        if self.get_class_by_token(jc_class.token) is not None:
            raise KeyError(f"Class with token {jc_class.token} is already present in the list of classes")
        self.classes.append(jc_class)

    @staticmethod
    def convert_aid(aid: str) -> str:
        aid_bytes = aid.split(":")
        result_aid = ""
        for aid_byte in aid_bytes:
            aid_byte_as_int = int(aid_byte, 0)
            result_aid += hex(aid_byte_as_int)[2:].rjust(2, "0")
        return result_aid

    @staticmethod
    def load_from_export_file(export_file_location: str) -> JCPackage | ValueError:
        with open(export_file_location, "r") as f:
            content = f.read().splitlines()

        # parsing package info
        package_info_passed = False
        package = None
        name = None
        for i, line in enumerate(content):
            if not "CONSTANT_Package_info" in line and not package_info_passed:
                continue
            elif "CONSTANT_Package_info" in line:
                package_info_passed = True
            elif package_info_passed:
                if "name_index" in line:
                    name = line.split("//")[1].strip().replace("/", ".")
                if "aid\t" in line:
                    aid = JCPackage.convert_aid(line.replace("aid", "").strip())
                    if name is None:
                        raise ValueError(f"name_index not found in {export_file_location}")
                    package = JCPackage(aid, name)
                    break

        if package is None:
            raise ValueError(f"aid not found in {export_file_location}")

        # parsing classes
        i = 0
        while i < len(content):
            if "class_info" in content[i]:
                i, jc_class = JCClass.load_from_export_file(content, i)
                package.add_class(jc_class)
            else:
                i += 1

        return package

    def __str__(self):
        result_string = ""
        result_string += f"Name: {self.name} ({self.aid.upper()})\n"
        result_string += "Classes:\n"
        for jc_class in self.classes:
            result_string += textwrap.indent(str(jc_class), "\t")
        return result_string


class ApiSpecification:
    def __init__(self):
        self.packages: list[JCPackage] = []

    def get_package_by_aid(self, aid: str) -> JCPackage | None:
        for package in self.packages:
            if package.aid == aid.lower():
                return package
        return None

    def get_package_by_name(self, name: str) -> JCPackage | None:
        for package in self.packages:
            if package.name == name:
                return package
        return None

    def add_package(self, package: JCPackage) -> Exception | None:
        if self.get_package_by_aid(package.aid) is not None:
            print(package.name)
            raise KeyError(f"Package with AID {package.aid} is already present in the list of packages")
        self.packages.append(package)

    @staticmethod
    def load_from_csv(csv_filename: str) -> ApiSpecification:
        import csv
        f = open(csv_filename, "r")
        csv_reader = csv.DictReader(f)

        specification = ApiSpecification()
        for row in csv_reader:
            if specification.get_package_by_aid(row['AID']) is None:
                package = JCPackage(row['AID'], row['package name'])
                specification.add_package(package)
            package = specification.get_package_by_aid(row['AID'])

            if package.get_class_by_token(int(row['class token'])) is None:
                jc_class = JCClass(int(row['class token']), row['class name'],
                                   JCAccessFlag.from_string(row['class access flags']))
                package.add_class(jc_class)
            jc_class = package.get_class_by_token(int(row['class token']))

            if row.get('method/field') is None:
                continue

            if row["method/field"] == "method":
                method = JCMethod(JCAccessFlag.from_string(row['access flags']), int(row['token']),
                                  row['name'], row['signature/type'])
                jc_class.add_method(method)
            if row["method/field"] == "field":
                field = JCField(row["name"], int(row["token"]), JCAccessFlag.from_string(row["access flags"]),
                                row["signature/type"], int(row["value"]))
                jc_class.add_field(field)

        return specification

    def export_to_csv(self, csv_name: str):
        f = open(csv_name, "w")
        csv_writer = csv.writer(f)

        header = ["AID", "package name", "class token", "class name", "class access flags", "method/field", "token",
                  "name", "access flags", "signature/type", "value"]
        csv_writer.writerow(header)

        for package in self.packages:
            if not package.classes:
                csv_writer.writerow([package.aid.upper(), package.name])
                continue
            for jc_class in package.classes:
                if not jc_class.methods and not jc_class.fields:
                    csv_writer.writerow([package.aid.upper(), package.name, jc_class.token, jc_class.name,
                                         JCAccessFlag.to_string(jc_class.access_flags)])
                    continue
                for method in jc_class.methods:
                    csv_writer.writerow([package.aid.upper(), package.name, jc_class.token, jc_class.name,
                                         JCAccessFlag.to_string(jc_class.access_flags), "method", method.token,
                                         method.name, JCAccessFlag.to_string(method.access_flags), method.signature])
                for field in jc_class.fields:
                    csv_writer.writerow([package.aid.upper(), package.name, jc_class.token, jc_class.name,
                                         JCAccessFlag.to_string(jc_class.access_flags), "field", field.token,
                                         field.name, JCAccessFlag.to_string(field.access_flags), field.jc_type,
                                         field.value])

    @staticmethod
    def load_from_export_files(export_files_locations: list[str]) -> ApiSpecification:
        api_specification = ApiSpecification()
        for export_file_location in export_files_locations:
            package = JCPackage.load_from_export_file(export_file_location)
            api_specification.add_package(package)
        return api_specification

    def __str__(self):
        result_string = ""
        for package in self.packages:
            result_string += str(package) + "\n\n"
        return result_string


if __name__ == "__main__":
    specification = ApiSpecification.load_from_export_files(
        ["/home/petr/Downloads/diplomka/deshmukh_thesis/jcAIDScan/jc212_kit/api_export_files/javacard/framework/javacard/framework_exp.tex"])
    specification.export_to_csv("test_javacard_framework.csv")
    new_specification = ApiSpecification.load_from_csv("test_javacard_framework.csv")
