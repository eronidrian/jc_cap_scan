from __future__ import annotations

import textwrap
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from api_specification.api_specification import JCAccessFlag, JCPackage, JCClass, JCMethod
from cap_parser.cap_parser_utils import Utils

if TYPE_CHECKING:
    from cap_parser.cap_file import CapFile
from cap_parser.component import Component, Structure
from cap_parser.constants import ComponentTags, CpInfoTags, API_SPECIFICATION


class Info(Structure, ABC):
    size = 3


class CpInfo(Structure, ABC):
    size = 1 + Info.size

    def __init__(self, cap_file: CapFile, info: Info):
        super().__init__(cap_file)
        self.info = info

    @property
    @abstractmethod
    def tag(self) -> int:
        pass

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> CpInfo | None:
        raw = raw[start_offset:]

        tag = raw[0]
        assert tag in CpInfoTags

        for cp_info_subclass in CpInfo.__subclasses__():
            if tag == cp_info_subclass.tag:
                return cp_info_subclass.load(cap_file, raw)

        print(f"CpInfo tag {tag} not implemented")
        return None

    def to_bytes(self) -> bytearray:
        raw = bytearray()
        raw.append(self.tag)
        raw.extend(self.info.to_bytes())
        return raw

    def __str__(self):
        return (f"{self.__class__.__name__}\n"
                f"{self.info}\n")


class ClassRef(Info, ABC):

    class Internal(Info):
        size = 2

        def __init__(self, cap_file: CapFile, internal_class_ref: int):
            super().__init__(cap_file)
            self.internal_class_ref = internal_class_ref

        @property
        def is_external(self):
            return False

        @staticmethod
        def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ClassRef.Internal:
            raw = raw[start_offset:]
            internal_class_ref = int.from_bytes(raw[0:2])
            return ClassRef.Internal(cap_file, internal_class_ref)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.extend(int.to_bytes(self.internal_class_ref, 2))
            return bytes(raw)

        def __str__(self):
            return f"Internal class ref: {self.internal_class_ref}\n"

    class External(Info):
        size = 2

        def __init__(self, cap_file: CapFile, package_token: int, class_token: int):
            super().__init__(cap_file)
            self.package_token = package_token
            self.class_token = class_token

        @property
        def is_external(self):
            return True

        @property
        def package(self) -> JCPackage | None:
            package_aid = self.cap_file.import_component.get_package_by_token(self.package_token).aid_hex
            package = API_SPECIFICATION.get_package_by_aid(package_aid)
            return package

        @property
        def _class(self) -> JCClass | None:
            if self.package is None:
                return None
            return self.package.get_class_by_token(self.class_token)

        @staticmethod
        def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ClassRef.External:
            raw = raw[start_offset:]
            package_token = raw[0] - 128
            class_token = raw[1]
            return ClassRef.External(cap_file, package_token, class_token)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(self.package_token + 128)
            raw.append(self.class_token)
            return bytes(raw)

        def __str__(self):
            return (f"Package token: {self.package_token} ({self.package.name if self.package is not None else 'not found in JC API'})\n"
                    f"Class token: {self.class_token} ({self._class.name if self._class is not None else 'not found in JC API'})\n")

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ClassRef.External | ClassRef.Internal:
        raw = raw[start_offset:]

        if raw[0] >= 128:  # high bit is one
            return ClassRef.External.load(cap_file, raw)
        else:
            return ClassRef.Internal.load(cap_file, raw)


class ClassRefInfo(CpInfo):
    padding = 0

    tag = CpInfoTags.CONSTANT_Classref

    def __init__(self, cap_file: CapFile, info: ClassRef.Internal | ClassRef.External):
        super().__init__(cap_file, info)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ClassRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_Classref
        assert raw[3] == ClassRefInfo.padding
        class_ref = ClassRef.load(cap_file, raw[1:])
        return ClassRefInfo(cap_file, class_ref)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.append(CpInfoTags.CONSTANT_Classref)
        raw.extend(self.info.to_bytes())
        raw.append(self.padding)
        return bytes(raw)


class InstanceFieldRef(Info):

    def __init__(self, cap_file: CapFile, class_ref: ClassRef.External | ClassRef.Internal, token: int):
        super().__init__(cap_file)
        self.class_ref = class_ref
        self.token = token

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> InstanceFieldRef:
        raw = raw[start_offset:]
        class_ref = ClassRef.load(cap_file, raw)
        token = raw[2]
        return InstanceFieldRef(cap_file, class_ref, token)

    def to_bytes(self) -> bytes:
        raw = bytearray()
        raw.extend(self.class_ref.to_bytes())
        raw.append(self.token)
        return bytes(raw)

    def __str__(self):
        return (f"{self.class_ref}"
                f"Token: {self.token}\n")


class InstanceFieldRefInfo(CpInfo):
    tag = CpInfoTags.CONSTANT_InstanceFieldref

    def __init__(self, cap_file: CapFile, info: InstanceFieldRef):
        super().__init__(cap_file, info)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> InstanceFieldRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_InstanceFieldref
        instance_field_ref = InstanceFieldRef.load(cap_file, raw[1:])
        return InstanceFieldRefInfo(cap_file, instance_field_ref)


class VirtualMethodRef(InstanceFieldRef):
    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> VirtualMethodRef:
        raw = raw[start_offset:]
        class_ref = ClassRef.load(cap_file, raw)
        token = raw[2]
        return VirtualMethodRef(cap_file, class_ref, token)

    @property
    def is_external(self) -> bool:
        return self.class_ref.is_external


    @property
    def _method(self) -> JCMethod | None:
        if not self.class_ref.is_external or self.class_ref._class is None:
            return None
        return self.class_ref._class.get_method_by_token_and_access_flags_subset(self.token, {JCAccessFlag.VIRTUAL})

    def __str__(self):
        if not self.class_ref.is_external:
            return (f"{self.class_ref}"
                    f"Token: {self.token}\n")

        return (f"{self.class_ref}"
                f"Token: {self.token} ({self._method.name if self._method is not None else 'not found in JC API'})\n")


class VirtualMethodRefInfo(CpInfo):
    tag = CpInfoTags.CONSTANT_VirtualMethodref

    def __init__(self, cap_file: CapFile, info: VirtualMethodRef):
        super().__init__(cap_file, info)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> VirtualMethodRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_VirtualMethodref
        virtual_method_ref = VirtualMethodRef.load(cap_file, raw[1:])
        return VirtualMethodRefInfo(cap_file, virtual_method_ref)



class StaticMethodRef(Info, ABC):
    class Internal(Info):
        padding = 0

        def __init__(self, cap_file: CapFile, offset: int):
            super().__init__(cap_file)
            self.offset = offset

        @property
        def is_external(self) -> bool:
            return False

        @staticmethod
        def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> StaticMethodRef.Internal:
            raw = raw[start_offset:]
            assert raw[0] == StaticMethodRef.Internal.padding
            offset = int.from_bytes(raw[1:3])
            return StaticMethodRef.Internal(cap_file, offset)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(StaticMethodRef.Internal.padding)
            raw.extend(int.to_bytes(self.offset, 2))
            return bytes(raw)

        def __str__(self):
            return f"Offset: {self.offset}\n"

    class External(Info):

        def __init__(self, cap_file: CapFile, package_token: int, class_token: int, token: int):
            super().__init__(cap_file)
            self.package_token = package_token
            self.class_token = class_token
            self.token = token

        @property
        def is_external(self) -> bool:
            return True

        @property
        def package(self) -> JCPackage | None:
            package_aid = self.cap_file.import_component.get_package_by_token(self.package_token).aid_hex
            package = API_SPECIFICATION.get_package_by_aid(package_aid)
            return package

        @property
        def _class(self) -> JCClass | None:
            if self.package is None:
                return None
            return self.package.get_class_by_token(self.class_token)

        @property
        def _method(self) -> JCMethod | None:
            if self._class is None:
                return None
            return self._class.get_method_by_token_and_access_flags_subset(self.token, {JCAccessFlag.STATIC})

        @staticmethod
        def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> StaticMethodRef.External:
            raw = raw[start_offset:]
            package_token = raw[0] - 128
            class_token = raw[1]
            token = raw[2]
            return StaticMethodRef.External(cap_file, package_token, class_token, token)

        def to_bytes(self) -> bytes:
            raw = bytearray()
            raw.append(self.package_token + 128)
            raw.append(self.class_token)
            raw.append(self.token)
            return bytes(raw)

        def __str__(self):
            return (f"Package token: {self.package_token} ({self.package.name if self.package is not None else 'not found in JC API'})\n"
                    f"Class token: {self.class_token} ({self._class.name if self._class is not None else 'not found in JC API'})\n"
                    f"Method token: {self.token} ({self._method.name if self._method is not None else 'not found in JC API'})\n")

    @staticmethod
    def load(cap_file: CapFile, raw: bytes,
             start_offset: int = 0) -> StaticMethodRef.Internal | StaticMethodRef.External:
        raw = raw[start_offset:]

        if raw[0] >= 128:  # high bit is one
            return StaticMethodRef.External.load(cap_file, raw)
        else:
            return StaticMethodRef.Internal.load(cap_file, raw)


class StaticMethodRefInfo(CpInfo):
    tag = CpInfoTags.CONSTANT_StaticMethodref

    def __init__(self, cap_file: CapFile, info: StaticMethodRef.Internal | StaticMethodRef.External):
        super().__init__(cap_file, info)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> StaticMethodRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == CpInfoTags.CONSTANT_StaticMethodref
        static_method_ref = StaticMethodRef.load(cap_file, raw[1:])
        return StaticMethodRefInfo(cap_file, static_method_ref)

class StaticFieldRef(StaticMethodRef, ABC):

    class External(StaticMethodRef.External):
        def __str__(self):
            package_aid = self.cap_file.import_component.get_package_by_token(self.package_token).aid_hex
            package_from_jc_api = API_SPECIFICATION.get_package_by_aid(package_aid)
            if package_from_jc_api is None:
                package_name = "not found in JC API"
                class_name = ""
            else:
                package_name = package_from_jc_api.name
                class_from_jc_api = package_from_jc_api.get_class_by_token(self.class_token)
                class_name = class_from_jc_api.name if class_from_jc_api is not None else "not found in JC API"

            return (f"Package token: {self.package_token} ({package_name})\n"
                    f"Class token: {self.class_token} ({class_name})\n"
                    f"Token: {self.token}\n")


class StaticFieldRefInfo(CpInfo):
    tag = CpInfoTags.CONSTANT_StaticFieldref

    def __init__(self, cap_file: CapFile, info: StaticFieldRef):
        super().__init__(cap_file, info)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> StaticFieldRefInfo:
        raw = raw[start_offset:]
        assert raw[0] == StaticFieldRefInfo.tag
        static_method_ref = StaticMethodRef.load(cap_file, raw[1:])
        return StaticFieldRefInfo(cap_file, static_method_ref)



class ConstantPoolComponent(Component):
    tag = ComponentTags.COMPONENT_ConstantPool
    filename = "ConstantPool.cap"

    def __init__(self, cap_file: CapFile, constant_pool: list[CpInfo]):
        super().__init__(cap_file)
        self.constant_pool = constant_pool

    @property
    def count(self) -> int:
        return len(self.constant_pool)

    @staticmethod
    def load(cap_file: CapFile, raw: bytes, start_offset: int = 0) -> ConstantPoolComponent:
        raw = raw[start_offset:]
        assert raw[0] == ConstantPoolComponent.tag

        count = int.from_bytes(raw[3:5])
        _, constant_pool = Utils.load_structure_array(cap_file, raw, 5, count, CpInfo)

        return ConstantPoolComponent(cap_file, constant_pool)

    def __str__(self):
        result_string = "Constant pool component\n\n"
        result_string += "Constant pool:\n"
        for cp_info in self.constant_pool:
            result_string += textwrap.indent(str(cp_info), "\t") + "\n"
        return result_string

    def pretty_print(self) -> None:
        print(self.__str__())

    @property
    def size(self) -> int:
        return 2 + CpInfo.size * self.count

    def to_bytes(self) -> bytes:
        raw = super().to_bytes()
        raw.extend(int.to_bytes(self.count, 2))
        for cp_info in self.constant_pool:
            raw.extend(cp_info.to_bytes())
        return bytes(raw)

    def get_cp_info_by_method_name(self, method_name: str) -> CpInfo | None:
        for cp_info in self.constant_pool:
            if cp_info.tag not in [CpInfoTags.CONSTANT_VirtualMethodref, CpInfoTags.CONSTANT_StaticMethodref]:
                continue
            if not cp_info.info.is_external:
                continue
            if cp_info.info._method is None:
                continue
            if cp_info.info._method.name.lower() == method_name:
                return cp_info
        return None

