from __future__ import annotations

import textwrap
from abc import abstractmethod, ABC

from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags, CpInfoTags


class Info(Structure, ABC):
    size = 3


class CpInfo(Structure, ABC):

    size = 1 + Info.size

    def __init__(self, info: Info):
        self.info = info

    @property
    @abstractmethod
    def tag(self) -> int:
        pass

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> CpInfo | None:
        raw = raw[start_offset:]

        tag = raw[0]
        assert tag in CpInfoTags

        for cp_info_subclass in CpInfo.__subclasses__():
            if tag == cp_info_subclass.tag:
                return cp_info_subclass.load(raw)

        print(f"CpInfo tag {tag} not implemented")
        return None


class ClassRef(Info, ABC):
    class Internal(Info):

        def __init__(self, internal_class_ref: int):
            self.internal_class_ref = internal_class_ref

        @staticmethod
        def load(raw: bytes, start_offset: int = 0) -> ClassRef.Internal:
            raw = raw[start_offset:]
            internal_class_ref = int.from_bytes(raw[0:2])
            return ClassRef.Internal(internal_class_ref)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.extend(int.to_bytes(self.internal_class_ref, 2))
            return bytes(raw)

        def __str__(self):
            return f"Internal class ref: {self.internal_class_ref}"

    class External(Info):

        def __init__(self, package_token: int, class_token: int):
            self.package_token = package_token
            self.class_token = class_token

        @staticmethod
        def load(raw: bytes, start_offset: int = 0) -> ClassRef.External:
            raw = raw[start_offset:]
            package_token = raw[0] - 128
            class_token = raw[1]
            return ClassRef.External(package_token, class_token)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(self.package_token + 128)
            raw.append(self.class_token)
            return bytes(raw)

        def __str__(self):
            return (f"Package token: {self.package_token}\n"
                    f"Class token: {self.class_token}")

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> ClassRef.External | ClassRef.Internal:
        raw = raw[start_offset:]

        if raw[0] >= 128:  # high bit is one
            return ClassRef.External.load(raw)
        else:
            return ClassRef.Internal.load(raw)


class ClassRefInfo(CpInfo):
    padding = 0

    tag = CpInfoTags.CONSTANT_Classref

    def __init__(self, info: ClassRef.Internal | ClassRef.External):
        super().__init__(info)

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> ClassRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_Classref
        assert raw[3] == ClassRefInfo.padding
        class_ref = ClassRef.load(raw[1:])
        return ClassRefInfo(class_ref)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(CpInfoTags.CONSTANT_Classref)
        raw.extend(self.info.to_bytes())
        raw.append(self.padding)
        return bytes(raw)


    def __str__(self):
        return (f"Classref_info\n"
                f"{self.info}\n")


class InstanceFieldRef(Info):

    def __init__(self, class_ref: ClassRef.External | ClassRef.Internal, token: int):
        self.class_ref = class_ref
        self.token = token

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> InstanceFieldRef:
        raw = raw[start_offset:]
        class_ref = ClassRef.load(raw)
        token = raw[2]
        return InstanceFieldRef(class_ref, token)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(self.class_ref.to_bytes())
        raw.append(self.token)
        return bytes(raw)

    def __str__(self):
        return (f"{self.class_ref}\n"
                f"Token: {self.token}\n")


class InstanceFieldRefInfo(CpInfo):
    tag = CpInfoTags.CONSTANT_InstanceFieldref

    def __init__(self, info: InstanceFieldRef):
        super().__init__(info)

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> InstanceFieldRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_InstanceFieldref
        instance_field_ref = InstanceFieldRef.load(raw[1:])
        return InstanceFieldRefInfo(instance_field_ref)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(CpInfoTags.CONSTANT_InstanceFieldref)
        raw.extend(self.info.to_bytes())
        return bytes(raw)

    def __str__(self):
        return (f"InstanceFieldref_info\n"
                f"{self.info}")

class VirtualMethodRef(InstanceFieldRef):
    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> VirtualMethodRef:
        raw = raw[start_offset:]
        class_ref = ClassRef.load(raw)
        token = raw[2]
        return VirtualMethodRef(class_ref, token)


class VirtualMethodRefInfo(CpInfo):
    tag = CpInfoTags.CONSTANT_VirtualMethodref

    def __init__(self, info: VirtualMethodRef):
        super().__init__(info)

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> VirtualMethodRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_VirtualMethodref
        virtual_method_ref = VirtualMethodRef.load(raw[1:])
        return VirtualMethodRefInfo(virtual_method_ref)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(CpInfoTags.CONSTANT_VirtualMethodref)
        raw.extend(self.info.to_bytes())
        return bytes(raw)

    def __str__(self):
        return (f"VirtualMethodref_info\n"
                f"{self.info}")

class StaticMethodRef(Info, ABC):
    class Internal(Info):
        padding = 0

        def __init__(self, offset: int):
            self.offset = offset

        @staticmethod
        def load(raw: bytes, start_offset: int = 0) -> StaticMethodRef.Internal:
            raw = raw[start_offset:]
            assert raw[0] == StaticMethodRef.Internal.padding
            offset = int.from_bytes(raw[1:3])
            return StaticMethodRef.Internal(offset)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(StaticMethodRef.Internal.padding)
            raw.extend(int.to_bytes(self.offset, 2))
            return bytes(raw)

        def __str__(self):
            return f"Offset: {self.offset}\n"

    class External(Info):

        def __init__(self, package_token: int, class_token: int, token: int):
            self.package_token = package_token
            self.class_token = class_token
            self.token = token

        @staticmethod
        def load(raw: bytes, start_offset: int = 0) -> StaticMethodRef.External:
            raw = raw[start_offset:]
            package_token = raw[0] - 128
            class_token = raw[1]
            token = raw[2]
            return StaticMethodRef.External(package_token, class_token, token)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(self.package_token + 128)
            raw.append(self.class_token)
            raw.append(self.token)
            return bytes(raw)

        def __str__(self):
            return (f"Package token: {self.package_token}\n"
                    f"Class token: {self.class_token}\n"
                    f"Method token: {self.token}\n")

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> StaticMethodRef.Internal | StaticMethodRef.External:
        raw = raw[start_offset:]

        if raw[0] >= 128: # high bit is one
            return StaticMethodRef.External.load(raw)
        else:
            return StaticMethodRef.Internal.load(raw)


class StaticMethodRefInfo(CpInfo):
    tag = CpInfoTags.CONSTANT_StaticMethodref

    def __init__(self, info: StaticMethodRef.Internal | StaticMethodRef.External):
        super().__init__(info)

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> StaticMethodRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_StaticMethodref
        static_method_ref = StaticMethodRef.load(raw[1:])
        return StaticMethodRefInfo(static_method_ref)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(CpInfoTags.CONSTANT_StaticMethodref)
        raw.extend(self.info.to_bytes())
        return bytes(raw)

    def __str__(self):
        return (f"StaticMethodref_info\n"
                f"{self.info}")




class ConstantPoolComponent(Component):
    tag = ComponentTags.COMPONENT_ConstantPool

    def __init__(self, constant_pool: list[CpInfo]):
        self.constant_pool = constant_pool

    @property
    def count(self) -> int:
        return len(self.constant_pool)

    @staticmethod
    def load(raw: bytes, start_offset: int = 0) -> ConstantPoolComponent:
        raw = raw[start_offset:]
        assert raw[0] == ConstantPoolComponent.tag

        count = int.from_bytes(raw[3:5])
        constant_pool = []
        offset = 0
        for _ in range(count):
            cp_info = CpInfo.load(raw[5:], offset)
            offset += cp_info.size
            constant_pool.append(cp_info)

        return ConstantPoolComponent(constant_pool)

    def pretty_print(self) -> None:
        print("Constant pool component")
        print()
        print("Constant pool:")
        for cp_info in self.constant_pool:
            print(textwrap.indent(str(cp_info), "\t"))
        pass

    @property
    def size(self) -> int:
        return 2 + CpInfo.size * self.count


    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(ConstantPoolComponent.tag)
        raw.extend(int.to_bytes(self.size, 2))
        raw.extend(int.to_bytes(self.count, 2))
        for cp_info in self.constant_pool:
            raw.extend(cp_info.to_bytes())
        return bytes(raw)


constant_pool_component = ConstantPoolComponent.load_from_file("../template_method/applets/javacard/ConstantPool.cap")
constant_pool_component.export_to_file("../ConstantPool.cap")
constant_pool_component = ConstantPoolComponent.load_from_file("../ConstantPool.cap")
constant_pool_component.pretty_print()
