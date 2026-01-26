from enum import IntEnum

from api_specification import ApiSpecification

component_names = [
    "Header",
    "Directory",
    "Applet",
    "Import",
    "ConstantPool",
    "Class",
    "Method",
    "StaticField",
    "ReferenceLocation",
    "Export",
    "Descriptor",
]

class ComponentTags(IntEnum):
    COMPONENT_Header = 1
    COMPONENT_Directory = 2
    COMPONENT_Applet = 3
    COMPONENT_Import = 4
    COMPONENT_ConstantPool = 5
    COMPONENT_Class = 6
    CONSTANT_Method = 7
    CONSTANT_StaticField = 8
    CONSTANT_ReferenceLocation = 9
    CONSTANT_Descriptor = 11

class CpInfoTags(IntEnum):
    CONSTANT_Classref = 1
    CONSTANT_InstanceFieldref = 2
    CONSTANT_VirtualMethodref = 3
    CONSTANT_SuperMethodref = 4
    CONSTANT_StaticFieldref = 5
    CONSTANT_StaticMethodref = 6

API_SPECIFICATION = ApiSpecification.load_from_csv("/home/petr/Downloads/diplomka/jc_api_tables/overview_table_305_new.csv")
