import json
import traceback
import tkinter as tk
import sys
import stat
import h5pickle, h5py
from tkinter import filedialog, messagebox

import tqdm

from padamo.node_lib import NodeView
from ..base import Tool
from .login_form import LoginForm
from padamo.ui_elements.button_panel import ButtonPanel
from .lazy_remote import LazyHDF5OnlineBindedReader

class HDFFactory(object):
    def __init__(self, ssh_connector, path):
        assert hasattr(ssh_connector, "make_connection")
        self.ssh_connector = ssh_connector
        self.path = path

    def __call__(self, field):
        return LazyHDF5OnlineBindedReader(self.ssh_connector, self.path, field)

def is_mat_file(sftp, path):
    attr = sftp.stat(path).st_mode
    return not stat.S_ISDIR(attr) and path.endswith(".mat")

def has_field(sftp, path, key):
    try:
        file_obj = sftp.open(path, "r", bufsize=65536)
        h5file = h5py.File(file_obj, "r")
        return key in h5file.keys()
    except PermissionError:
        return False

def create_metric(sftp,key):
    def metric(filepath):
        file_obj = sftp.open(filepath, "r", bufsize=65536)
        h5file = h5py.File(file_obj, "r")
        res = float(h5file[key][0])
        h5file.close()
        return res
    return metric

def scalarize_sftp(sftp,key, filepath):
    file_obj = sftp.open(filepath, "r")
    h5file = h5py.File(file_obj, "r")
    res = float(h5file[key][0])
    h5file.close()
    return res

class HDFDirFactory(object):
    def __init__(self, connector, path, time_key="unixtime_dbl_global"):
        self.ssh_connector = connector
        self.time_key = time_key
        self.ssh, self.sftp = self.ssh_connector.make_connection()
        self.files = None
        self.path = path

    def __call__(self, field):
        if self.files is None:
            files = self.sftp.listdir(self.path)
            files = [self.path + "/" + item for item in tqdm.tqdm(files) if is_mat_file(self.sftp, self.path + "/" + item)]
            #files = [item for item in tqdm.tqdm(files) ]
            filemetrics = [(scalarize_sftp(self.sftp,self.time_key,item),item) for item in tqdm.tqdm(files) if has_field(self.sftp, item, self.time_key)]
            filemetrics.sort(key=lambda x: x[0])
            self.files = [item[1] for item in filemetrics]
            print(files)

        x = None
        for file in tqdm.tqdm(self.files):
            next_part = LazyHDF5OnlineBindedReader(self.ssh_connector, file, field)
            if x is None:
                x = next_part
            else:
                x = x.extend(next_part)
        return x


class RemoteExplorer(Tool):
    TAB_LABEL = "Remote"

    def __init__(self, master, globals_):
        Tool.__init__(self,master, globals_)
        rpanel = tk.Frame(self)
        rpanel.pack(side="right",fill="y")
        bpanel = ButtonPanel(rpanel)
        bpanel.pack(side="top",fill="x")
        bpanel.add_button("Connect", self.on_connect, 0)

        self.lform = LoginForm(rpanel)
        self.lform.pack(side="bottom", fill="both", expand=True)

        mainpanel = tk.Frame(self)
        mainpanel.pack(side="left", fill="both",expand=True)
        self.ssh = None
        self.connector = None
        self.sftp = None

        self.explorer_listbox = tk.Listbox(mainpanel)
        self.explorer_listbox.pack(side="bottom", fill="both", expand=True)
        self.explorer_listbox.bind('<Double-1>', self.on_dblclick)
        self.path_var = tk.StringVar(self)
        self.path_stack = []
        topview = tk.Label(mainpanel, textvariable=self.path_var)
        topview.pack(side="top", fill="x")
        self.globals["loaded_remote"] = None
        self.globals["loaded_remote_dir"] = None

    def on_connect(self):
        try:
            self.ssh, self.sftp = self.lform.create_connection()
            self.connector = self.lform.create_connector()
        except:
            print("Connection error")
            print(traceback.format_exc())

        self.path_var.set("/")
        self.path_stack.clear()
        self.reset_listing()

    def on_dblclick(self, event):
        if self.sftp is not None:
            sel = self.explorer_listbox.selection_get()
            #print(sel)
            if sel=="..":
                self.path_stack.pop(-1)
                newpath = "/"+"/".join(self.path_stack)
                self.path_var.set(newpath)
                self.reset_listing()
            else:
                newpath = "/"+"/".join(self.path_stack)+"/"+sel
                attr = self.sftp.stat(newpath).st_mode
                if stat.S_ISDIR(attr):
                    self.path_stack.append(sel)
                    newpath = "/" + "/".join(self.path_stack)
                    self.path_var.set(newpath)
                    self.reset_listing()
                else:
                    self.set_global("loaded_remote", HDFFactory(self.connector, newpath))

    def set_directory(self,path):
        self.globals["loaded_remote_dir"] = HDFDirFactory(self.connector, path)

    def reset_listing(self):
        listpath = self.path_var.get()
        self.explorer_listbox.delete(0,tk.END)
        if listpath != "/":
            self.explorer_listbox.insert(tk.END,"..")
        if self.sftp is not None:
            for item in sorted(self.sftp.listdir(listpath)):
                self.explorer_listbox.insert(tk.END,item)
            self.set_directory(listpath)
