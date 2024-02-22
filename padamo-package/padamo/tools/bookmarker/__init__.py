import tkinter as tk
from ..base import Tool
from padamo.bookmarking import BookmarkStorage, Bookmark
from padamo.bookmarking.lazy_file_bookmarks import BookmarkBinaryFileStorage
from padamo.ui_elements.button_panel import ButtonPanel

class Bookmarker(Tool):
    TAB_LABEL = "Bookmarks"
    
    def __init__(self,master, globals_):
        super().__init__(master, globals_)
        self.storage = BookmarkBinaryFileStorage()
        self.bookmark_list = tk.Listbox(self)
        self.bookmark_list.pack(side="left", fill="y")
        self.sync_marks()
        rpanel = tk.Frame(self)
        rpanel.pack(side="right", fill="both", expand=True)
        self.entry = tk.Text(rpanel)
        self.mark_var = tk.StringVar(self)
        tk.Label(rpanel, textvariable=self.mark_var).pack(side="top", fill="x")
        self.entry.pack(expand=True, fill="both")
        self.bookmark_list.bind('<<ListboxSelect>>', self.on_select)
        self._selected_item = None
        button_panel = ButtonPanel(rpanel)
        button_panel.pack(side="bottom", fill="x")
        button_panel.add_button("Delete", self.on_delete,0)
        button_panel.add_button("Copy timestamp", self.on_copy,0)

    def on_delete(self):
        if self._selected_item is not None:
            self.storage.pop(self._selected_item)
            self.select_new_index(None,flush=False)
            self.sync_marks()

    def on_copy(self):
        if self._selected_item is not None:
            item:Bookmark = self.storage.get_bookmark(self._selected_item)
            stamp = item.make_timestamp()
            self.clipboard_clear()
            self.clipboard_append(stamp)


    def on_select(self, event):
        w = event.widget
        if w.curselection():
            index = int(w.curselection()[0])
            self.select_new_index(index)

    def select_new_index(self, index,flush=True):
        if flush:
            self._flush_bookmark()
        self._selected_item = index
        self._update_selected_item()

    def _flush_bookmark(self):
        if self._selected_item is not None:
            #self.storage.trigger_change()
            bookmark = self.storage.get_bookmark(self._selected_item)
            bookmark.description = self.entry.get("1.0",tk.END)
            self.storage.set_bookmark(self._selected_item, bookmark)
            #self.storage.bookmarks[self._selected_item].description = self.entry.get("1.0",tk.END)

    def _update_selected_item(self):
        self.entry.delete("1.0",tk.END)
        if self._selected_item is None:
            self.mark_var.set("")
        else:
            current_mark = self.storage.get_bookmark(self._selected_item)
            current_mark:Bookmark
            self.entry.insert(tk.END,current_mark.description)
            self.mark_var.set(current_mark.make_timestamp())
            print(current_mark.make_timestamp())

    def save_bookmarks(self):
        self._flush_bookmark()
        self.storage.truncate()
        self.storage.file_handler.flush()

    def sync_marks(self):
        self.bookmark_list.delete(0,tk.END)
        for x in self.storage.get_bookmark_list():
            self.bookmark_list.insert(tk.END, x)

    def add_mark(self, mark):
        self.storage.append_bookmark(mark)
        self.sync_marks()
        self.select_new_index(None)
