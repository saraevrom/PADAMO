import json
import os.path as ospath
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import os, re

from padamo.appdata import USER_DATA_DIR


CONF_PATH = ospath.join(USER_DATA_DIR, "workspace.json")


def get_extensions(file_types):
    res = []
    for item in file_types:
        res += re.findall(r"\.\w+", item[1])
    print("ACCEPTED EXTENSIONS", res)
    return res
    #return [re.findall(r"\.\w+", item[1]) for item in file_types]

def add_extension(filename:str, extensions):
    if not filename:
        return filename
    check_passed = False
    candidate = ""
    for ext in extensions:
        if ext:
            if not candidate:
                candidate = ext
            if filename.endswith(ext):
                check_passed = True
                print("Extension check passed")
                break
    if not check_passed and candidate:
        print("Automatically added extension", candidate)
        filename = filename + candidate
    return filename


class Workspace(object):
    WORKSPACE_DIR = None

    def __init__(self, subspace):
        self.subspace = subspace

    @classmethod
    def get_workspace_dir(cls):
        if cls.WORKSPACE_DIR:
            return cls.WORKSPACE_DIR
        else:
            return "."
    def get_tgt_dir(self):
        if self.WORKSPACE_DIR:
            return ospath.join(self.WORKSPACE_DIR, self.subspace)
        else:
            return self.subspace

    def __call__(self, subdir):
        tgt = self.ensure_directory()
        if tgt:
            return os.path.join(tgt,subdir)
        return subdir

    def populate(self):
        pass

    def ensure_directory(self):
        if self.WORKSPACE_DIR:
            tgt_dir = self.get_tgt_dir()
            if not os.path.isdir(tgt_dir):
                os.makedirs(tgt_dir)
                self.populate()
            return tgt_dir
        return None

    def _modify_kwargs(self, kwargs):
        cwd = self.ensure_directory()
        if cwd:
            kwargs["initialdir"] = cwd

    def askopenfilename(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        return filedialog.askopenfilename(*args, **kwargs)

    def get_file(self, filename):
        cwd = self.ensure_directory()
        if cwd:
            filepath = os.path.join(cwd, filename)
            return filepath

    def askdirectory(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        return filedialog.askdirectory(*args, **kwargs)

    def asksaveasfilename(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        filename = filedialog.asksaveasfilename(*args, **kwargs)
        extensions = get_extensions(kwargs["filetypes"])
        filename = add_extension(filename, extensions)
        return filename

    def askopenfilenames(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        return filedialog.askopenfilenames(*args, **kwargs)

    @classmethod
    def initialize_workspace(cls, force=False):
        if ospath.isfile(CONF_PATH) and not force:
            with open(CONF_PATH, "r") as fp:
                cls.WORKSPACE_DIR = json.load(fp)["workspace"]
        else:
            # messagebox.showinfo(
            #     title="Workspace setup",
            #     message="Choose the workspace directory"
            # )
            workspace_dir = filedialog.askdirectory(initialdir=".",
                                                    title="Choose the workspace directory")
            if not workspace_dir:
                workspace_dir = None
            print("Selected workspace", workspace_dir)
            with open(CONF_PATH, "w") as fp:
                json.dump({"workspace": workspace_dir}, fp)
            cls.WORKSPACE_DIR = workspace_dir

