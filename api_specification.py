from __future__ import annotations
from enum import Enum


class JCMethodType(Enum):
    STATIC = 0
    VIRTUAL = 1

    @staticmethod
    def from_string(type_string: str) -> JCMethodType | Exception:
        if type_string == 'static':
            return JCMethodType(JCMethodType.STATIC)
        if type_string == 'virtual':
            return JCMethodType(JCMethodType.VIRTUAL)
        raise ValueError(f"Type string {type_string} is not 'static' nor 'virtual'")


class JCMethod:
    def __init__(self, method_type: JCMethodType, token: int, name: str, signature: str):
        self.method_type = method_type
        self.token = token
        self.name = name
        self.signature = signature.lower()


class JCClass:
    def __init__(self, token: int, name: str):
        self.token = token
        self.name = name
        self.methods: list[JCMethod] = []

    @property
    def virtual_methods(self) -> list[JCMethod]:
        return [method for method in self.methods if method.method_type == JCMethodType.VIRTUAL]

    @property
    def static_methods(self) -> list[JCMethod]:
        return [method for method in self.methods if method.method_type == JCMethodType.STATIC]

    def get_method_by_token_and_type(self, token: int, method_type: JCMethodType) -> JCMethod | None:
        for method in self.methods:
            if method.token == token and method.method_type == method_type:
                return method
        return None

    def add_method(self, method: JCMethod) -> Exception | None:
        if self.get_method_by_token_and_type(method.token, method.method_type) is not None:
            raise KeyError(
                f"Method with token {method.token} and type {method.method_type} is already present in the list of methods")
        self.methods.append(method)


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
                jc_class = JCClass(int(row['class token']), row['class name'])
                package.add_class(jc_class)
            jc_class = package.get_class_by_token(int(row['class token']))

            if row.get('method token') is None:
                continue

            method = JCMethod(JCMethodType.from_string(row['method type']), int(row['method token']),
                              row['method name'], row['method signature'])
            jc_class.add_method(method)

        return specification
