from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from cap_parser.bytecodes import BYTECODE_MAP
from cap_parser.cap_parser_utils import Utils

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags


class ExceptionHandlerInfo(Structure):

    def __init__(self, cap_file: CapFile, start_offset: int, stop_bit: bool, active_length: int, handler_offset: int,
                 catch_type_index: int):
        super().__init__(cap_file)
        self.start_offset = start_offset
        self.stop_bit = stop_bit
        self.active_length = active_length
        self.handler_offset = handler_offset
        self.catch_type_index = catch_type_index

    @property
    def end_offset(self) -> int:
        return self.start_offset + self.active_length

    @property
    def size(self) -> int:
        return 8

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ExceptionHandlerInfo:
        raw = raw[start_offset:]
        _start_offset = int.from_bytes(raw[0:2])
        stop_bit = bool(raw[2] >> 7)  # highest bit
        active_length = int.from_bytes(raw[2:4]) & 0x7fff  # rest of the bits
        handler_offset = int.from_bytes(raw[4:6])
        catch_type_index = int.from_bytes(raw[6:8])

        return ExceptionHandlerInfo(cap_file, _start_offset, stop_bit, active_length, handler_offset, catch_type_index)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(int.to_bytes(self.start_offset, 2))
        active_length = self.active_length if not self.stop_bit else (self.active_length | 0x8000)
        raw.extend(int.to_bytes(active_length, 2))
        raw.extend(int.to_bytes(self.handler_offset, 2))
        raw.extend(int.to_bytes(self.catch_type_index, 2))
        return bytes(raw)

    def __str__(self):
        return (f"Start offset: {self.start_offset}\n"
                f"Stop bit: {self.stop_bit}\n"
                f"Active length: {self.active_length}\n"
                f"Handler offset: {self.handler_offset}\n"
                f"Catch type index: {self.catch_type_index}\n")


class MethodHeaderInfo(Structure):
    flag_masks = {
        "ACC_ABSTRACT": 0x04,
        "ACC_EXTENDED": 0x08
    }
    size = 2

    def __init__(self, cap_file: CapFile, flags: int, max_stack: int, nargs: int, max_locals: int):
        super().__init__(cap_file)
        self.flags = flags
        self.max_stack = max_stack
        self.nargs = nargs
        self.max_locals = max_locals

    @property
    def flags_str(self) -> str:
        flags_str = []
        for flag_name in MethodHeaderInfo.flag_masks:
            if Utils.is_flag_set(self.flags, MethodHeaderInfo.flag_masks, flag_name):
                flags_str.append(flag_name)
        return ",".join(flags_str)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> MethodHeaderInfo:
        raw = raw[start_offset:]

        flags = (raw[0] & 0xf0) >> 4
        max_stack = raw[0] & 0x0f
        nargs = (raw[1] & 0xf0) >> 4
        max_locals = raw[1] & 0x0f

        return MethodHeaderInfo(cap_file, flags, max_stack, nargs, max_locals)

    def to_bytes(self) -> bytes:
        raw = bytearray()

        flags = self.flags << 4 | self.max_stack
        raw.append(flags)
        nargs = self.nargs << 4 | self.max_locals
        raw.append(nargs)
        return bytes(raw)

    def __str__(self):
        return (f"Flags: {self.flags} ({self.flags_str})\n"
                f"Max stack: {self.max_stack}\n"
                f"Nargs: {self.nargs}\n"
                f"Max locals: {self.max_locals}\n")


class MethodInfo(Structure):

    def __init__(self, cap_file: CapFile, method_header: MethodHeaderInfo, bytecodes: bytes):
        super().__init__(cap_file)
        self.method_header = method_header
        self.bytecodes = bytecodes

    @property
    def size(self) -> int:
        return self.method_header.size + len(self.bytecodes)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> MethodInfo:
        raw = raw[start_offset:]
        method_header = MethodHeaderInfo.load(cap_file, raw)
        bytecodes = raw[method_header.size:]
        return MethodInfo(cap_file, method_header, bytecodes)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(self.method_header.to_bytes())
        raw.extend(self.bytecodes)
        return bytes(raw)

    def __str__(self):
        result_string = "Method header:\n"
        result_string += textwrap.indent(str(self.method_header), "\t")
        result_string += f"Bytecodes:\n"
        for bytecode in self.bytecodes:
            result_string += f"{textwrap.indent(BYTECODE_MAP.get(bytecode, hex(bytecode)), '\t')}\n"
        return result_string


class MethodComponent(Component):
    tag = ComponentTags.CONSTANT_Method
    filename = "Method.cap"

    def __init__(self, cap_file: CapFile, exception_handlers: list[ExceptionHandlerInfo], methods: list[MethodInfo]):
        super().__init__(cap_file)
        self.exception_handlers = exception_handlers
        self.methods = methods

    @property
    def handler_count(self) -> int:
        return len(self.exception_handlers)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> MethodComponent:
        raw = raw[start_offset:]
        assert raw[0] == MethodComponent.tag

        handler_count = raw[3]
        offset = 4
        offset, exception_handlers = Utils.load_structure_array(cap_file, raw, offset, handler_count, ExceptionHandlerInfo)

        methods = []
        while offset < len(raw):
            method = MethodInfo.load(cap_file, raw, offset)
            offset += method.size
            methods.append(method)

        return MethodComponent(cap_file, exception_handlers, methods)

    def __str__(self):
        result_string = "Method component\n\n"
        result_string += "Exception handlers:\n"
        for exception_handler in self.exception_handlers:
            result_string += textwrap.indent(str(exception_handler), "\t") + "\n"
        result_string += "Methods:\n"
        for method in self.methods:
            result_string += textwrap.indent(str(method), "\t") + "\n"
        return result_string

    def pretty_print(self) -> None:
        print(self.__str__())

    @property
    def size(self) -> int:
        return 1 + Utils.size_of_structure_array(self.exception_handlers) + Utils.size_of_structure_array(self.methods)

    def to_bytes(self) -> bytes:
        raw = super().to_bytes()
        raw.append(self.handler_count)
        for exception_handler in self.exception_handlers:
            raw.extend(exception_handler.to_bytes())
        for method in self.methods:
            raw.extend(method.to_bytes())
        return bytes(raw)

    def get_method_at_offset(self, cap_file: CapFile, offset: int, bytecode_count: int) -> MethodInfo:
        assert offset + MethodHeaderInfo.size + bytecode_count <= self.size

        offset += 3 # skip tag and size
        raw = self.to_bytes()
        return MethodInfo.load(cap_file, raw[offset : offset + MethodHeaderInfo.size + bytecode_count])


