import os
import json
from .bookmark import Bookmark
from padamo.appdata import DIRECTORIES

BOOKMARKS_FILE = os.path.join(DIRECTORIES.user_data_dir,"bookmarks.json")

class BookmarkStorage(object):
    def __init__(self):
        self.bookmarks = []
        self.load_bookmarks()
        self._changed = False

    def trigger_change(self):
        self._changed = True

    def add_bookmark(self, item):
        self.bookmarks.append(item)
        self.bookmarks.sort(key=lambda x: x.sort_key())
        self._changed = True

    def remove_bookmark(self, index):
        self.bookmarks.pop(index)
        self._changed = True

    def load_bookmarks(self):
        if os.path.isfile(BOOKMARKS_FILE):
            self.bookmarks.clear()
            with open(BOOKMARKS_FILE, "r") as fp:
                data = json.load(fp)
                for bookmark_data in data:
                    self.bookmarks.append(Bookmark.deserialize(bookmark_data))

    def save_bookmarks(self):
        if self._changed:
            data = [item.serialize() for item in self.bookmarks]
            with open(BOOKMARKS_FILE,"w") as fp:
                json.dump(data, fp)
            print("Bookmarks saved")

    def get_bookmark_list(self):
        return [item.title() for item in self.bookmarks]