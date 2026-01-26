import shutil

static_or_virtual = "virtual"
class_name = "keypair"
method_name = "getprivate"
call_or_return = "return"

shutil.rmtree("template_method.zip", ignore_errors=True)
# shutil.rmtree("template_method", ignore_errors=True)
# shutil.rmtree("template_method_backup", ignore_errors=True)

shutil.copy("SimpleApplet/src/applets/SimpleApplet.java", f"{static_or_virtual}_{class_name}_{method_name}_{call_or_return}.java")
shutil.copy("SimpleApplet/!uploader/SimpleApplet.cap", "./template_method.zip")
shutil.unpack_archive("template_method.zip", f"template_{static_or_virtual}_{class_name}_{method_name}_{call_or_return}")
# shutil.copytree("template_method", "template_method_backup")