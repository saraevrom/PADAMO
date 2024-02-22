import os
import inspect
import pkgutil
import importlib
import sys

from padamo.node_processing import Node
from .base import ModuleLoadError
from .addons_workspace import ADDONS_WORKSPACE
from padamo.appdata import USER_DATA_DIR
from padamo import node_lib
MPL_CACHEDIR = os.path.join(USER_DATA_DIR,"mpl_cache")
os.environ["MPLCONFIGDIR"] = MPL_CACHEDIR

files = pkgutil.iter_modules(node_lib.__path__)
files = ["padamo.node_lib."+f[1] for f in files if f[1].startswith("node_")]

NODES = []
NODE_DICT = {}


def scan_mod(mod, prefix=""):
    attrs = dir(mod)
    for i in attrs:
        obj = getattr(mod, i)
        if inspect.isclass(obj) and issubclass(obj, Node) and obj.LOCATION:
            if prefix:
                if obj.LOCATION.startswith("/"):
                    obj.LOCATION = prefix+obj.LOCATION
                else:
                    obj.LOCATION = prefix + "/" + obj.LOCATION
            NODES.append(obj)
            NODE_DICT[obj.get_identifier()] = obj

for f in files:
    try:
        mod = importlib.import_module(f)
    except ModuleLoadError:
        print("Skipped module", f)
        mod = None
    if mod is not None:
        scan_mod(mod)


NODES.sort(key=lambda x: x.LOCATION)

# print("Inline nodes:")
# for n in NODES:
#     print(f"\t{n.LOCATION}")

del files


def load_addons():
    ADDONS_DIR = ADDONS_WORKSPACE.ensure_directory()
    if ADDONS_DIR:
        print("Getting Addons")
        ss = os.listdir(ADDONS_DIR)
        sys.path.insert(0, ADDONS_DIR)
        for s in ss:
            if s.startswith("addon_"):
                print("Addon:", s, " ", end="")
                try:
                    addon_name = os.path.splitext(s)[0]
                    mod = __import__(addon_name, None, None, [''])
                    scan_mod(mod,prefix="/Addons/"+addon_name[len('addon_'):])
                except Exception as e:
                    print(str(e))
                print("OK")
        NODES.sort(key=lambda x: x.LOCATION)
        print("Done")
    else:
        print("Addons dir is not set")