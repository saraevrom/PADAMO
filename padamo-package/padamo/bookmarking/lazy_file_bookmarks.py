import os, io
from padamo.appdata import DIRECTORIES
from .bookmark import Bookmark

TIMESTAMP_LENGTH=47
COMMENT_LENGTH=209

ENTRY_LENGTH = TIMESTAMP_LENGTH+COMMENT_LENGTH

BOOKMARKS_FILE = os.path.join(DIRECTORIES.user_data_dir,"bookmarks.dat")


def encode_entry(item_str):
    item_str_encoded = item_str.encode("UTF-8")
    assert len(item_str_encoded) <= ENTRY_LENGTH
    fillers = ENTRY_LENGTH - len(item_str_encoded)
    item_str_encoded += b'\x00' * fillers
    return item_str_encoded


class BookmarkBinaryFileStorage(object):
    def __init__(self, filename=BOOKMARKS_FILE):
        if not os.path.isfile(filename):
            touched = open(filename, "wb")
            touched.close()
        self.file_handler = open(filename, "r+b")
        self.filename = filename
        self._length = self.capacity()

    def capacity(self):
        assert os.path.getsize(self.filename) % ENTRY_LENGTH == 0
        return os.path.getsize(self.filename) // ENTRY_LENGTH

    def truncate(self):
        if self.capacity() > self._length:
            self.file_handler.truncate(self._length*ENTRY_LENGTH)
            self.file_handler.flush()

    # def __del__(self):
    #     self.truncate()
    #     self.file_handler.close()

    def __len__(self):
        return self._length

    def append(self, item_str:str):
        item_str_encoded = encode_entry(item_str)
        self.file_handler.write(item_str_encoded)
        self.file_handler.flush()
        self._length += 1

    def pop(self,item):
        if item < 0:
            item = self._length-item
        if item >= self._length or item<0:
            raise IndexError(f"Index {item} is out of range {self._length}")

        popped = self[item]
        for i in range(item, self._length-1):
            self[i] = self[i+1]

        self._length -= 1
        self.truncate()
        return popped

    def __getitem__(self, item):
        if item<0:
            item = self._length-item
        if item>=self._length or item<0:
            raise IndexError(f"Index {item} is out of range {self._length}")
        position = item*ENTRY_LENGTH
        self.file_handler.seek(position)
        recovered = self.file_handler.read(ENTRY_LENGTH)
        last_i = ENTRY_LENGTH-1
        while recovered[last_i]==b"\x00":
            last_i -= 1
        recovered = recovered[:last_i+1]
        return recovered.decode("UTF-8")

    def __setitem__(self, key, value):
        if key<0:
            key = self._length-key
        if key>=self._length or key<0:
            raise IndexError(f"Index {key} is out of range {self._length}")
        position = key * ENTRY_LENGTH
        encoded = encode_entry(value)
        self.file_handler.seek(position)
        self.file_handler.write(encoded)
        self.file_handler.flush()

    def get_bookmark(self,i):
        entry = self[i]
        return Bookmark.deserialize_string(entry)

    def set_bookmark(self, i, bookmark: Bookmark):
        entry = bookmark.serialize_string()
        self[i] = entry

    def append_bookmark(self, bookmark: Bookmark):
        entry = bookmark.serialize_string()
        self.append(entry)

    def pop_bookmark(self, item):
        entry = self.pop(item)
        return Bookmark.deserialize_string(entry)

    def get_bookmark_list(self):
        return [self.get_bookmark(i).title() for i in range(self._length)]