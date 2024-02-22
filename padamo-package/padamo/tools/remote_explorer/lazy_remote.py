import gc

import h5pickle
import h5py
import numpy as np
from padamo.lazy_array_operations import LazyArrayOperation
from .login_form import Connector

class LazyHDF5OnlineBindedReader(LazyArrayOperation):
    def __init__(self, ssh_connector:Connector, filename, field):
        self.ssh_connector = ssh_connector
        self.ssh = None #self.ssh_connector.make_connection()
        self.sftp = None #self.ssh.open_sftp()
        self.filename = filename
        self.field = field
        self._file = None
        self._is_pickled = False
        self.ensure_file()

    def ensure_connection(self):
        if self.ssh is None:
            self.ssh, self.sftp = self.ssh_connector.make_connection()

    def _get_h5(self):
        if self._is_pickled:
            ssh = self.ssh_connector.make_connection()
            sftp = ssh.open_sftp()
            file_obj = sftp.open(self.filename, "r", bufsize=65536)
            return h5py.File(file_obj,"r")
        else:
            self.ensure_file()
            return self._file

    def ensure_file(self, force=False):
        self.ensure_connection()
        if self._file is None or force:
            file_obj = self.sftp.open(self.filename,"r", bufsize=65536)
            print(file_obj)
            file_obj.seek(0)
            self._file = h5py.File(file_obj, "r")

    def request_data(self, interesting_slices):
        #print("H5",interesting_slices)
        # self.ensure_file(True)
        _file = self._get_h5()
        res = np.array(_file[self.field][interesting_slices])
        #print("REMOTE REQUEST", interesting_slices, _file[self.field].shape)
        if self._is_pickled:
            gc.collect()
        #print("RETURNS", res)
        return res

    def shape(self):
        # self.ensure_file(True)
        _file = self._get_h5()
        s = _file[self.field].shape
        if self._is_pickled:
            gc.collect()
        return s

    def __getstate__(self):
        state = {
            "filename":self.filename,
            "field":self.field,
            "connector":self.ssh_connector.get_state()
        }
        print("Pickled lazy remote")
        return state

    def __setstate__(self, state):
        self._is_pickled = False
        self.ssh_connector = Connector(**state["connector"])
        self.ssh = None
        self.sftp = None
        #self.ssh = self.ssh_connector.make_connection()
        #self.sftp = self.ssh.open_sftp()
        self.filename = state["filename"]
        self.field = state["field"]
        self._file = None
        #self._is_pickled = True
        #self.ensure_file()
        print("Unpickled lazy remote")
