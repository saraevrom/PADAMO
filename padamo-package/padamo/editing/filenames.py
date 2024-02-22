from tkinter.filedialog import askopenfilename


class Filename(object):
    DEFAULT_EXTENSION=""
    FILETYPES = []

class ANYFILE(Filename):
    DEFAULT_EXTENSION = ""
    FILETYPES = [("Any file", "*.*")]

class TEXTFILE(Filename):
    DEFAULT_EXTENSION = "*.txt"
    FILETYPES = [("Text file", "*.txt")]


class HDF5FILE(Filename):
    DEFAULT_EXTENSION = "*.h5"
    FILETYPES = [("Text file", "*.h5")]