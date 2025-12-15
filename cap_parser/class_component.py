from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

from cap_parser.cap_parser_utils import Utils
from cap_parser.constants import API_SPECIFICATION
from cap_parser.constant_pool_component import ClassRef

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags


class TypeDescriptor(Structure):
    jc_type_to_string_map = {
        "0": "",
        "1": "void",
        "2": "boolean",
        "3": "byte",
        "4": "short",
        "5": "int",
        "6": "reference",
        "a": "boolean[]",
        "b": "byte[]",
        "c": "short[]",
        "d": "int[]",
        "e": "reference[]"
    }
    string_to_type_map = dict((v, k) for k, v in jc_type_to_string_map.items())
    string_to_type_map[""] = ""

    def __init__(self, cap_file: CapFile, nibble_count: int, _type: bytes):
        super().__init__(cap_file)
        self.nibble_count = nibble_count
        self._type = _type

    @property
    def size(self) -> int:
        return 1 + len(self._type)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> TypeDescriptor:
        raw = raw[start_offset:]
        nibble_count = raw[0]
        _type = raw[1: int((nibble_count + 1) / 2) + 1]
        return TypeDescriptor(cap_file, nibble_count, _type)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(self.nibble_count)
        raw.extend(self._type)
        return bytes(raw)

    def __str__(self):
        _type = self._type.hex()
        _type = _type if self.nibble_count % 2 == 0 else _type[:-1]
        type_strings = []
        i = 0
        while i < len(_type):
            type_string = TypeDescriptor.jc_type_to_string_map.get(_type[i], "?")
            if "reference" in type_string:
                reference = _type[i + 1: i + 5]
                package_token = int(reference[:2], 16) - 128
                package_aid = self.cap_file.import_component.get_package_by_token(package_token).aid_hex
                package = API_SPECIFICATION.get_package_by_aid(package_aid)
                class_token = int(reference[2:], 16)
                jc_class = package.get_class_by_token(class_token)

                if '[]' in type_string:
                    reference_string = f"{package.name}.{jc_class.name}[]"
                else:
                    reference_string = f"{package.name}.{jc_class.name}"

                type_strings.append(reference_string)
                i += 5
            else:
                type_strings.append(type_string)
                i += 1

        return f"{type_strings[-1]}({';'.join(type_strings[:-1])})"

    @staticmethod
    def reference_name_to_reference(cap_file: CapFile, reference_name: str) -> str:
        reference_name_split = reference_name.split(".")
        class_name = reference_name_split[-1]
        package_name = ".".join(reference_name_split[:-1])

        package = API_SPECIFICATION.get_package_by_name(package_name)
        if package is None:
            raise ValueError(f"Package with name {package_name} not found in specification")
        try:
            package_token = cap_file.import_component.get_token_by_package_aid(package.aid)
        except ValueError:
            raise ValueError(f"Package with AID {package.aid} not found in Import component")

        _class = package.get_class_by_name(class_name)
        if _class is None:
            raise ValueError(f"Class with name {class_name} not found in the specification")

        hex_package_token = hex(package_token + 128)[2:]
        hex_class_token = hex(_class.token)[2:].zfill(2)

        return hex_package_token + hex_class_token

    @staticmethod
    def from_string(cap_file: CapFile, signature_string: str) -> TypeDescriptor:
        result = re.search(r'(.*)\((.*)\)', signature_string)
        return_value = result.group(1)
        parameters = result.group(2)
        parameters = parameters.split(";")
        type_strings = parameters + [return_value]
        _type = ""
        for type_string in type_strings:
            if type_string in TypeDescriptor.string_to_type_map.keys():
                _type += TypeDescriptor.string_to_type_map[type_string]
            elif re.match(r'[.a-zA-Z$]+\[]', type_string):
                _type += TypeDescriptor.string_to_type_map["reference[]"]
                _type += TypeDescriptor.reference_name_to_reference(cap_file, type_string[:-2])
            elif re.match(r'[.a-zA-Z$]+', type_string):
                _type += TypeDescriptor.string_to_type_map["reference"]
                _type += TypeDescriptor.reference_name_to_reference(cap_file, type_string)
            else:
                raise ValueError(f"Unrecognized type string: {type_string}")

        jc_type_len = len(_type)
        _type = _type if jc_type_len % 2 == 0 else _type + "0"

        return TypeDescriptor(cap_file, jc_type_len, bytes.fromhex(_type))

    def __eq__(self, other: TypeDescriptor) -> bool:
        return self.size == other.size and self._type == other._type



class InterfaceInfo(Structure):
    flag_masks = {
        "ACC_INTERFACE": 0x08,
        "ACC_SHAREABLE": 0x04,
        "ACC_REMOTE": 0x02
    }

    def __init__(self, cap_file: CapFile, flags: int, superinterfaces: list[ClassRef], interface_name: str | None):
        super().__init__(cap_file)
        self.flags = flags
        self.superinterfaces = superinterfaces
        self.interface_name = interface_name

    @property
    def interface_count(self) -> int:
        return len(self.superinterfaces)

    @property
    def interface_name_length(self) -> int:
        if self.interface_name is None:
            return 0
        return len(self.interface_name.encode("utf-8"))

    @property
    def flags_str(self) -> str:
        flags_str = []
        for flag_name in InterfaceInfo.flag_masks:
            if Utils.is_flag_set(self.flags, InterfaceInfo.flag_masks, flag_name):
                flags_str.append(flag_name)
        return ",".join(flags_str)

    @property
    def size(self) -> int:
        size = 1 + Utils.size_of_structure_array(self.superinterfaces)
        if Utils.is_flag_set(self.flags, InterfaceInfo.flag_masks, "ACC_REMOTE"):
            size += 1 + self.interface_name_length
        return size

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> InterfaceInfo:
        raw = raw[start_offset:]
        flags = raw[0] >> 4
        assert Utils.is_flag_set(flags, InterfaceInfo.flag_masks, "ACC_INTERFACE")

        interface_count = raw[0] & 0xf
        offset, superinterfaces = Utils.load_structure_array(cap_file, raw, 1, interface_count, ClassRef)

        if Utils.is_flag_set(flags, InterfaceInfo.flag_masks, "ACC_REMOTE"):
            interface_name = None
        else:
            interface_name_length = raw[offset]
            offset += 1
            interface_name = raw[offset: offset + interface_name_length].decode('utf-8')

        return InterfaceInfo(cap_file, flags, superinterfaces, interface_name)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(self.flags << 4 | self.interface_count)
        for superinterface in self.superinterfaces:
            raw.extend(superinterface.to_bytes())
        if not Utils.is_flag_set(self.flags, InterfaceInfo.flag_masks, "ACC_REMOTE"):
            raw.append(self.interface_name_length)
            raw.extend(self.interface_name.encode('utf-8'))
        return bytes(raw)

    def __str__(self):
        result_string = ""
        result_string += f"Flags: {self.flags} ({self.flags_str})\n"
        result_string += f"Superinterfaces:\n"
        for superinterface in self.superinterfaces:
            result_string += f"{superinterface}\n"
        result_string += f"Interface name: {self.interface_name}\n"
        return result_string


class ImplementedInterfaceInfo(Structure):

    def __init__(self, cap_file: CapFile, interface: ClassRef.Internal | ClassRef.External, index: list[int]):
        super().__init__(cap_file)
        self.interface = interface
        self.index = index

    @property
    def count(self) -> int:
        return len(self.index)

    @property
    def size(self) -> int:
        return self.interface.size + 1 + self.count

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ImplementedInterfaceInfo:
        raw = raw[start_offset:]

        interface = ClassRef.load(cap_file, raw)
        offset = interface.size
        count = raw[offset]
        offset += 1
        index = list(raw[offset: offset + count])

        return ImplementedInterfaceInfo(cap_file, interface, index)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(self.interface.to_bytes())
        raw.append(self.count)
        for item in self.index:
            raw.append(item)
        return bytes(raw)


class RemoteMethodInfo(Structure):

    def __init__(self, cap_file: CapFile, remote_method_hash: bytes, signature_offset: int, virtual_method_token: int):
        super().__init__(cap_file)
        self.remote_method_hash = remote_method_hash
        self.signature_offset = signature_offset
        self.virtual_method_token = virtual_method_token

    @property
    def size(self) -> int:
        return 5

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> RemoteMethodInfo:
        raw = raw[start_offset:]

        remote_method_hash = raw[0:2]
        signature_offset = int.from_bytes(raw[2:4])
        virtual_method_token = raw[4]

        return RemoteMethodInfo(cap_file, remote_method_hash, signature_offset, virtual_method_token)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(self.remote_method_hash)
        raw.extend(int.to_bytes(self.signature_offset, 2))
        raw.append(self.virtual_method_token)
        return bytes(raw)


class ClassInfo(Structure):
    flag_masks = InterfaceInfo.flag_masks

    def __init__(self, cap_file: CapFile, flags: int, super_class_ref: ClassRef | None, declared_instance_size: int,
                 first_reference_token: int | None, reference_count: int, public_method_table_base: int,
                 package_method_table_base: int, public_virtual_method_table: list[int | None],
                 package_virtual_method_table: list[int], interfaces: list[ImplementedInterfaceInfo]):
        super().__init__(cap_file)
        self.flags = flags
        self.super_class_ref = super_class_ref
        self.declared_instance_size = declared_instance_size
        self.first_reference_token = first_reference_token
        self.reference_count = reference_count
        self.public_method_table_base = public_method_table_base
        self.package_method_table_base = package_method_table_base
        self.public_virtual_method_table = public_virtual_method_table
        self.package_virtual_method_table = package_virtual_method_table
        self.interfaces = interfaces

    @property
    def flags_str(self) -> str:
        flags_str = []
        for flag_name in ClassInfo.flag_masks:
            if Utils.is_flag_set(self.flags, ClassInfo.flag_masks, flag_name):
                flags_str.append(flag_name)
        return ",".join(flags_str)

    @property
    def interface_count(self) -> int:
        return len(self.interfaces)

    @property
    def public_method_table_count(self) -> int:
        return len(self.public_virtual_method_table)

    @property
    def package_method_table_count(self) -> int:
        return len(self.package_virtual_method_table)

    @property
    def size(self) -> int:
        size = 1 + self.super_class_ref.size + 7 + 2 * self.public_method_table_count + 2 * self.package_method_table_count + Utils.size_of_structure_array(
            self.interfaces)
        return size

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ClassInfo:
        raw = raw[start_offset:]
        flags = raw[0] >> 4
        assert not Utils.is_flag_set(flags, ClassInfo.flag_masks, "ACC_INTERFACE")
        interface_count = raw[0] & 0xf

        if int.from_bytes(raw[1:3]) == 0xffff:
            super_class_ref = None
            offset = 3
        else:
            super_class_ref = ClassRef.load(cap_file, raw[1:])
            offset = 1 + super_class_ref.size

        attributes = {}
        attribute_names = ["declared_instance_size", "first_reference_token", "reference_count",
                           "public_method_table_base", "public_method_table_count", "package_method_table_base",
                           "package_method_table_count"]
        for attribute in attribute_names:
            attributes[attribute] = raw[offset]
            offset += 1

        offset, public_virtual_method_table = Utils.load_u2_array(raw, offset, attributes["public_method_table_count"])
        offset, package_virtual_method_table = Utils.load_u2_array(raw, offset, attributes["package_method_table_count"])
        offset, interfaces = Utils.load_structure_array(cap_file, raw, offset, interface_count, ImplementedInterfaceInfo)


        return ClassInfo(cap_file, flags, super_class_ref, attributes["declared_instance_size"],
                         attributes["first_reference_token"],
                         attributes["reference_count"], attributes["public_method_table_base"],
                         attributes["package_method_table_base"],
                         public_virtual_method_table, package_virtual_method_table, interfaces)

    def to_bytes(self) -> bytearray:
        raw = bytearray()
        raw.append(self.flags << 4 | self.interface_count)
        raw.extend(self.super_class_ref.to_bytes() if self.super_class_ref is not None else b'\xff\xff')
        raw.append(self.declared_instance_size)
        raw.append(self.first_reference_token if self.first_reference_token is not None else 0xff)
        raw.append(self.reference_count)
        raw.append(self.public_method_table_base)
        raw.append(self.public_method_table_count)
        raw.append(self.package_method_table_base)
        raw.append(self.package_method_table_count)
        for entry in self.public_virtual_method_table:
            raw.extend(int.to_bytes(entry if entry is not None else 0xffff, 2))
        for entry in self.package_virtual_method_table:
            raw.extend(int.to_bytes(entry, 2))
        for interface in self.interfaces:
            raw.extend(interface.to_bytes())
        return raw

    def __str__(self):
        result_string = (f"Flags: {self.flags} ({self.flags_str})\n"
                         f"Superclass ref:\n"
                         f"{textwrap.indent(str(self.super_class_ref), '\t')}\n"
                         f"Declared instance size: {self.declared_instance_size}\n"
                         f"First reference token: {self.first_reference_token}\n"
                         f"Reference count: {self.reference_count}\n"
                         f"Public method table base: {self.public_method_table_base}\n"
                         f"Package method table base: {self.package_method_table_base}\n"
                         f"Public virtual method table: {self.public_virtual_method_table}\n"
                         f"Package virtual method table: {self.package_virtual_method_table}\n")
        result_string += f"Interfaces:\n"
        for interface in self.interfaces:
            result_string += textwrap.indent(str(interface), "\t")
        return result_string


class ClassComponent(Component):
    tag = ComponentTags.COMPONENT_Class
    filename = "Class.cap"

    def __init__(self, cap_file: CapFile, interfaces: list[InterfaceInfo],
                 classes: list[ClassInfo]):
        super().__init__(cap_file)
        self.interfaces = interfaces
        self.classes = classes

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ClassComponent:
        raw = raw[start_offset:]
        assert raw[0] == ClassComponent.tag

        offset = 3
        interfaces = []
        classes = []
        while offset < len(raw):
            try:
                interface = InterfaceInfo.load(cap_file, raw, offset)
                offset += interface.size
                interfaces.append(interface)
            except AssertionError:
                jc_class = ClassInfo.load(cap_file, raw, offset)
                offset += jc_class.size
                classes.append(jc_class)

        return ClassComponent(cap_file, interfaces, classes)

    def pretty_print(self) -> None:
        print("Class component")
        print()
        print("Interfaces:")
        for interface in self.interfaces:
            print(textwrap.indent(str(interface), "\t"))
        print("Classes:")
        for jc_class in self.classes:
            print(textwrap.indent(str(jc_class), "\t"))

        pass

    @property
    def size(self) -> int:
        return Utils.size_of_structure_array(self.interfaces) + Utils.size_of_structure_array(self.classes)

    def to_bytes(self) -> bytearray:
        raw = super().to_bytes()
        for interface in self.interfaces:
            raw.extend(interface.to_bytes())
        for _class in self.classes:
            raw.extend(_class.to_bytes())
        return raw
