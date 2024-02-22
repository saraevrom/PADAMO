import os
import tkinter as tk
import atexit
import json

import paramiko

from padamo.editing.widgets import IntegerEntry
from padamo.appdata import DIRECTORIES

CACHEFILE = os.path.join(DIRECTORIES.user_data_dir, "remote_data.json")


class PersistentConnection(object):
    conn_dict = dict()
    @classmethod
    def create_connection(cls, conn):
        if conn not in cls.conn_dict.keys():
            ssh_conn =  conn.make_new_connection()
            sftp_conn = ssh_conn.open_sftp()
            cls.conn_dict[conn] = ssh_conn, sftp_conn
            print("Made new connection:",conn)
        else:
            print("Reused connection:", conn)
        return cls.conn_dict[conn]

    @classmethod
    def reset(cls):
        print("Multiprocessing memory barrier is invoked")
        cls.conn_dict = dict()


class Connector(object):
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password

    def __repr__(self):
        return f"{self.user}@{self.host}:{self.port}"

    def __hash__(self):
        return hash((self.host,self.port,self.user,self.password))

    def __eq__(self, other):
        ok = True
        ok = ok and self.host == other.host
        ok = ok and self.port == other.port
        ok = ok and self.user == other.user
        ok = ok and self.password == other.password
        return ok

    def make_connection(self):
        return PersistentConnection.create_connection(self)

    def make_new_connection(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.host, self.port, self.user, self.password, timeout=10)
        return ssh

    def get_state(self):
        return self.__dict__.copy()


class LoginForm(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        tk.Label(self, text="Host").grid(row=0, column=0, sticky="nsw")
        self.hostvar = tk.StringVar(self)
        host_entry = tk.Entry(self,textvariable=self.hostvar)
        host_entry.grid(row=0, column=1, sticky="nsew")

        tk.Label(self, text="Port").grid(row=1, column=0, sticky="nsw")
        self.portvar = tk.StringVar(self)
        self.portvar.set("22")
        port_entry = IntegerEntry(self, textvariable=self.portvar)
        port_entry.grid(row=1, column=1, sticky="nsew")

        tk.Label(self,text="Login").grid(row=2,column=0,sticky="nsw")
        self.loginvar = tk.StringVar(self)
        login_entry = tk.Entry(self, textvariable=self.loginvar)
        login_entry.grid(row=2, column=1, sticky="nsew")

        tk.Label(self,text="Password").grid(row=3,column=0,sticky="nsw")

        self.passvar = tk.StringVar(self)
        pass_entry = tk.Entry(self, textvariable=self.passvar, show="*")
        pass_entry.grid(row=3, column=1, sticky="nsew")

        self.columnconfigure(1,weight=1)

        if os.path.isfile(CACHEFILE):
            with open(CACHEFILE, "r") as fp:
                data = json.load(fp)
                self.hostvar.set(data["host"])
                self.portvar.set(data["port"])
                self.loginvar.set(data["login"])

        atexit.register(self.save_cache)

    def __del__(self):
        atexit.unregister(self.save_cache)
        self.save_cache()

    def save_cache(self):
        data = {
            "host":self.hostvar.get(),
            "port":self.portvar.get(),
            "login":self.loginvar.get()
        }
        with open(CACHEFILE, "w") as fp:
            json.dump(data, fp)

    def create_connector(self):
        return Connector(self.hostvar.get(), self.portvar.get(), self.loginvar.get(), self.passvar.get())

    def create_connection(self):
        conn = self.create_connector()
        return conn.make_connection()
