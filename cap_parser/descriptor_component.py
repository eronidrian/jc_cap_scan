from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from cap_parser.cap_parser_utils import Utils
from cap_parser.class_component import TypeDescriptor
from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags
from cap_parser.constant_pool_component import ClassRef, StaticFieldRef, InstanceFieldRef
from cap_parser.method_component import MethodInfo

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile


class FieldDescriptorInfo(Structure):
    flag_masks = {"ACC_PUBLIC": 0x01,
                  "ACC_PRIVATE": 0x02,
                  "ACC_PROTECTED": 0x04,
                  "ACC_STATIC": 0x08,
                  "ACC_FINAL": 0x10}

    def __init__(self, cap_file: CapFile, token: int, access_flags: int, field_ref: StaticFieldRef | InstanceFieldRef,
                 _type: bytes):
        super().__init__(cap_file)
        self.token = token
        self.access_flags = access_flags
        self.field_ref = field_ref
        self._type = _type  # TODO: maybe change to special class

    @property
    def access_flags_str(self) -> str:
        flags_str = []
        for flag_name in FieldDescriptorInfo.flag_masks:
            if Utils.is_flag_set(self.access_flags, FieldDescriptorInfo.flag_masks, flag_name):
                flags_str.append(flag_name)
        return ",".join(flags_str)

    @property
    def size(self) -> int:
        return 2 + self.field_ref.size + 2

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> FieldDescriptorInfo:
        raw = raw[start_offset:]
        token = raw[0]
        access_flags = raw[1]
        # print(hex(access_flags))
        if Utils.is_flag_set(access_flags, FieldDescriptorInfo.flag_masks, "ACC_STATIC"):
            field_ref = StaticFieldRef.load(cap_file, raw, 2)
        else:
            field_ref = InstanceFieldRef.load(cap_file, raw, 2)
        offset = 2 + field_ref.size
        _type = raw[offset: offset + 2]
        return FieldDescriptorInfo(cap_file, token, access_flags, field_ref, _type)

    def to_bytes(self) -> bytearray:
        raw = bytearray()
        raw.append(self.token)
        raw.append(self.access_flags)
        raw.extend(self.field_ref.to_bytes())
        raw.extend(self._type)
        return raw

    def __str__(self):
        return (f"Token: {self.token}\n"
                f"Access flags: {self.access_flags} ({self.access_flags_str})\n"
                f"Field ref:\n"
                f"{textwrap.indent(str(self.field_ref), '\t')}"
                f"Type: {self._type.hex()}\n")


class MethodDescriptorInfo(Structure):
    flag_masks = {
        "ACC_PUBLIC": 0x01,
        "ACC_PRIVATE": 0x02,
        "ACC_PROTECTED": 0x04,
        "ACC_STATIC": 0x08,
        "ACC_FINAL": 0x10,
        "ACC_ABSTRACT": 0x40,
        "ACC_INIT": 0x80,
    }

    def __init__(self, cap_file: CapFile, token: int, access_flags: int, method_offset: int, type_offset: int, bytecode_count: int,
                 exception_handler_count: int, exception_handler_index: int):

        super().__init__(cap_file)
        self.token = token
        self.access_flags = access_flags
        self.method_offset = method_offset
        self.type_offset = type_offset
        self.bytecode_count = bytecode_count
        self.exception_handler_count = exception_handler_count
        self.exception_handler_index = exception_handler_index

    @property
    def access_flags_str(self) -> str:
        flags_str = []
        for flag_name in MethodDescriptorInfo.flag_masks:
            if Utils.is_flag_set(self.access_flags, MethodDescriptorInfo.flag_masks, flag_name):
                flags_str.append(flag_name)
        return ",".join(flags_str)

    @property
    def method_info(self) -> MethodInfo:
        return self.cap_file.method_component.get_method_at_offset(self.cap_file, self.method_offset, self.bytecode_count)

    @property
    def type(self) -> TypeDescriptor:
        return self.cap_file.descriptor_component.types.get_type_at_offset(self.cap_file, self.type_offset)

    @property
    def size(self) -> int:
        return 12

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> MethodDescriptorInfo:
        raw = raw[start_offset:]
        token = raw[0]
        access_flags = raw[1]
        method_offset = int.from_bytes(raw[2:4])
        type_offset = int.from_bytes(raw[4:6])
        bytecode_count = int.from_bytes(raw[6:8])
        exception_handler_count = int.from_bytes(raw[8:10])
        exception_handler_index = int.from_bytes(raw[10:12])
        return MethodDescriptorInfo(cap_file, token, access_flags, method_offset, type_offset, bytecode_count,
                                    exception_handler_count, exception_handler_index)

    def to_bytes(self) -> bytearray:
        raw = bytearray()
        raw.append(self.token)
        raw.append(self.access_flags)
        raw.extend(int.to_bytes(self.method_offset, 2))
        raw.extend(int.to_bytes(self.type_offset, 2))
        raw.extend(int.to_bytes(self.bytecode_count, 2))
        raw.extend(int.to_bytes(self.exception_handler_count, 2))
        raw.extend(int.to_bytes(self.exception_handler_index, 2))
        return raw

    def __str__(self):
        return (f"Token: {self.token}\n"
                f"Access flags: {self.access_flags} ({self.access_flags_str})\n"
                f"Method info:\n"
                f"{textwrap.indent(str(self.method_info), '\t')}"
                f"Type: {self.type}\n"
                f"Exception handler count: {self.exception_handler_count}\n"
                f"Exception handler index: {self.exception_handler_index}\n")

class ClassDescriptorInfo(Structure):
    flag_masks = {
        "ACC_PUBLIC": 0x01,
        "ACC_FINAL": 0x10,
        "ACC_INTERFACE": 0x40,
        "ACC_ABSTRACT": 0x80
    }

    def __init__(self, cap_file: CapFile, token: int, access_flags: int,
                 this_class_ref: ClassRef.Internal | ClassRef.External, interfaces: list[ClassRef],
                 fields: list[FieldDescriptorInfo], methods: list[MethodDescriptorInfo]):
        super().__init__(cap_file)
        self.token = token
        self.access_flags = access_flags
        self.this_class_ref = this_class_ref
        self.interfaces = interfaces
        self.fields = fields
        self.methods = methods

    @property
    def interface_count(self) -> int:
        return len(self.interfaces)

    @property
    def field_count(self) -> int:
        return len(self.fields)

    @property
    def method_count(self) -> int:
        return len(self.methods)

    @property
    def access_flags_str(self) -> str:
        flags_str = []
        for flag_name in ClassDescriptorInfo.flag_masks:
            if Utils.is_flag_set(self.access_flags, ClassDescriptorInfo.flag_masks, flag_name):
                flags_str.append(flag_name)
        return ",".join(flags_str)

    @property
    def size(self) -> int:
        return 2 + self.this_class_ref.size + 5 + sum([interface.size for interface in self.interfaces]) + sum(
            [field.size for field in self.fields]) + sum([method.size for method in self.methods])

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ClassDescriptorInfo:
        raw = raw[start_offset:]
        token = raw[0]
        access_flags = raw[1]
        offset = 2
        this_class_ref = ClassRef.load(cap_file, raw, offset)
        offset += this_class_ref.size
        # print("class ref size: ", this_class_ref.size)
        interface_count = raw[offset]
        offset += 1
        field_count = int.from_bytes(raw[offset: offset + 2])
        offset += 2
        method_count = int.from_bytes(raw[offset: offset + 2])
        offset += 2

        offset, interfaces = Utils.load_structure_array(cap_file, raw, offset, interface_count, ClassRef)
        offset, fields = Utils.load_structure_array(cap_file, raw, offset, field_count, FieldDescriptorInfo)
        _, methods = Utils.load_structure_array(cap_file, raw, offset, method_count, MethodDescriptorInfo)

        return ClassDescriptorInfo(cap_file, token, access_flags, this_class_ref, interfaces, fields, methods)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(self.token)
        raw.append(self.access_flags)
        raw.extend(self.this_class_ref.to_bytes())
        raw.append(self.interface_count)
        raw.extend(int.to_bytes(self.field_count, 2))
        raw.extend(int.to_bytes(self.method_count, 2))
        raw.extend(Utils.structure_list_to_bytes(self.interfaces))
        raw.extend(Utils.structure_list_to_bytes(self.fields))
        raw.extend(Utils.structure_list_to_bytes(self.methods))
        return raw

    def __str__(self):
        result_string = (f"Token: {self.token}\n"
                         f"Access flags: {self.access_flags} ({self.access_flags_str})\n"
                         f"This class ref:\n")
        result_string += textwrap.indent(str(self.this_class_ref), "\t")
        result_string += "Interfaces:\n"
        for interface in self.interfaces:
            result_string += f"{textwrap.indent(str(interface), '\t')}\n"
        result_string += "Fields:\n"
        for field in self.fields:
            result_string += f"{textwrap.indent(str(field), '\t')}\n"
        result_string += "Methods:\n"
        for method in self.methods:
            result_string += f"{textwrap.indent(str(method), '\t')}\n"
        return result_string


class TypeDescriptorInfo(Structure):

    def __init__(self, cap_file: CapFile, constant_pool_type_descriptors: list[TypeDescriptor | None]):
        super().__init__(cap_file)
        self.constant_pool_type_descriptors = constant_pool_type_descriptors

    @property
    def constant_pool_types(self) -> list[int]:
        offset = 2 + 2 * len(self.constant_pool_type_descriptors)
        constant_pool_types = []

        for type_descriptor in self.constant_pool_type_descriptors:
            if type_descriptor is None:
                constant_pool_types.append(0xffff)
            else:
                type_descriptor_found_index = self.type_desc.index(type_descriptor)
                length_of_previous = Utils.size_of_structure_array(self.type_desc[:type_descriptor_found_index])
                constant_pool_types.append(offset + length_of_previous)

        return constant_pool_types

    @property
    def type_desc(self) -> list[TypeDescriptor]:
        type_desc = []
        for constant_pool_type_descriptor in self.constant_pool_type_descriptors:
            if constant_pool_type_descriptor is not None and constant_pool_type_descriptor not in type_desc:
                type_desc.append(constant_pool_type_descriptor)

        return type_desc

    @property
    def constant_pool_count(self) -> int:
        return len(self.constant_pool_types)

    @property
    def size(self) -> int:
        return 2 + 2 * self.constant_pool_count + Utils.size_of_structure_array(self.type_desc)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> TypeDescriptorInfo:
        raw = raw[start_offset:]
        constant_pool_count = int.from_bytes(raw[0:2])

        _, constant_pool_types = Utils.load_u2_array(raw, 2, constant_pool_count)
        constant_pool_type_descriptors = []
        for offset in constant_pool_types:
            if offset == 0xffff:
                type_descriptor = None
            else:
                type_descriptor = TypeDescriptor.load(cap_file, raw, offset)
            constant_pool_type_descriptors.append(type_descriptor)

        return TypeDescriptorInfo(cap_file, constant_pool_type_descriptors)

    def to_bytes(self) -> bytearray:
        raw = bytearray()
        raw.extend(int.to_bytes(self.constant_pool_count, 2))
        for cp_type in self.constant_pool_types:
            raw.extend(int.to_bytes(cp_type, 2))
        for type_descriptor in self.type_desc:
            raw.extend(type_descriptor.to_bytes())
        return raw

    def __str__(self):
        result_string = f"Constant pool type descriptors:\n"
        for i, type_descriptor in enumerate(self.constant_pool_type_descriptors):
            result_string += f"{i} - {type_descriptor}\n"
        return result_string

    def get_type_at_offset(self, cap_file: CapFile, offset: int) -> TypeDescriptor:
        assert offset < self.size
        raw = self.to_bytes()

        type_descriptor = TypeDescriptor.load(cap_file, raw, offset)
        return type_descriptor



class DescriptorComponent(Component):
    tag = ComponentTags.CONSTANT_Descriptor
    filename = "Descriptor.cap"

    def __init__(self, cap_file: CapFile, classes: list[ClassDescriptorInfo], types: TypeDescriptorInfo):
        super().__init__(cap_file)
        self.classes = classes
        self.types = types

    @property
    def class_count(self) -> int:
        return len(self.classes)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> DescriptorComponent:
        raw = raw[start_offset:]
        assert raw[0] == DescriptorComponent.tag

        class_count = raw[3]
        offset, classes = Utils.load_structure_array(cap_file, raw, 4, class_count, ClassDescriptorInfo)

        types = TypeDescriptorInfo.load(cap_file, raw, offset)
        return DescriptorComponent(cap_file, classes, types)

    def pretty_print(self) -> None:
        print("Descriptor component")
        print()
        print("Classes:")
        for _class in self.classes:
            print(textwrap.indent(str(_class), "\t"))
        print("Types:")
        print(textwrap.indent(str(self.types), "\t"))

    @property
    def size(self) -> int:
        return 1 + Utils.size_of_structure_array(self.classes) + self.types.size

    def to_bytes(self) -> bytes:
        raw = super().to_bytes()
        raw.append(self.class_count)
        raw.extend(Utils.structure_list_to_bytes(self.classes))
        raw.extend(self.types.to_bytes())
        return bytes(raw)
