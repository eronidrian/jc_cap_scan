from cap_parser.cap_file import CapFile

cap_file = CapFile.load_from_directory("/home/petr/Downloads/diplomka/jc_cap_scan/template_virtual_keypair_getprivate_return/applets/javacard")
cap_file.constant_pool_component.pretty_print()