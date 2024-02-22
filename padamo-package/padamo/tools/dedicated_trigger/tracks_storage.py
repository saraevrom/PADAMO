import tkinter as tk
from .storage import ConservativeStorage, IntervalStorage, ArrayStorage


class Storing(object):
    def __init__(self):
        self.storage = None

    def disconnect_storage(self):
        if self.storage:
            self.storage.on_take = None
            self.storage.on_store = None
        self.storage = None
        self.on_change()

    def set_storage(self, new_storage: ConservativeStorage):
        self.storage = new_storage
        self.storage.on_store = self.on_change
        self.storage.on_take = self.on_change
        self.on_change()

    def deserialize_inplace(self, obj):
        self.storage.deserialize_inplace(obj)
        self.on_change()

    def deserialize_disconnected(self, obj, cls):
        self.set_storage(cls.deserialize(obj))

    def serialize(self):
        return self.storage.serialize()


class DisplayStorage(tk.Frame, Storing):
    def __init__(self, master, label):
        tk.Frame.__init__(self, master)
        Storing.__init__(self)
        label = tk.Label(self,text=label)
        label.pack(side="top", fill=tk.X)
        self.listbox = tk.Listbox(self)
        self.listbox.bind('<<ListboxSelect>>', self.on_listbox_select)
        self.listbox.pack(side="bottom", fill=tk.BOTH, expand=True)
        self.propose_item_function = None
        self.select_callback = None

    def get_selected(self):
        sel = self.listbox.curselection()
        if sel:
            return sel[0]
        return None

    def on_change(self):
        if self.storage:
            intervals = self.storage.get_available()
            self.listbox.delete(0,tk.END)
            for item in intervals:
                self.listbox.insert(tk.END, str(item))

            if self.storage.last_index is not None and 0<=self.storage.last_index<len(intervals):
                self.listbox.see(self.storage.last_index)
        else:
            self.listbox.delete(0, tk.END)


    def clear(self):
        self.storage.clear()
        self.on_change()

    def on_listbox_select(self, event):
        cursel = self.listbox.curselection()
        if cursel:
            index = cursel[0]
            if self.select_callback is not None:
                self.select_callback(index)
                # if isinstance(self.storage, IntervalStorage):
                #     arg = self.storage.get_available()[index]
                # elif isinstance(self.storage, ArrayStorage):
                #     arg = index
                # else:
                #     return
                # item = self.storage.take_external(arg)
                # if not self.propose_item_function(item, self.storage):
                #     self.storage.store_external(item)
                #     self.listbox.selection_clear(0, tk.END)
            #
            # self.on_change()
            # if cursel:
            #     index = cursel[0]
            #     if index<self.listbox.size():
            #         self.listbox.see(index)

    # def display_diagram(self, source, ffmodel: FlatFieldingModel, preprocessor: DataThreeStagePreProcessor, broken,
    #                     phase_cutter=None):
    #     xs = []
    #     ys = []
    #     for interval in self.storage.get_available():
    #         data = source["data0"][interval.to_slice()]
    #         xs.append(interval.length())
    #         if ffmodel is not None:
    #             data = ffmodel.apply_nobreak(data)
    #         data = preprocessor.preprocess_whole(data, broken)
    #         ys.append(np.max(data))
    #     fig, ax = plt.subplots()
    #     ax.scatter(xs,ys)
    #     if phase_cutter is not None and ys:
    #         phase_cutter.draw_on_plot(ax, max(ys))
    #     fig.show()
