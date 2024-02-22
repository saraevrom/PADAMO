import tkinter as tk
from tkinter import ttk
from .tk_forms import ScrollView as ScrollableFrame
from .tk_forms import Validatable
from .modified_base import EntryWithEnterKey, SpinboxWithEnterKey

# This mess will be refactored

class SettingFormatError(Exception):
    def __init__(self, setting, action):
        self.failed_setting = setting
        self.failed_action = action
        super(SettingFormatError, self).__init__(f"Error {action} {setting}")


class Setting(tk.Frame):
    def __init__(self, master, setting_key, initial_value, sensitive=False):
        super(Setting, self).__init__(master)
        self.setting_key = setting_key
        self.initial_value = initial_value
        self.build_setting(self)
        self.reset()
        self.sensitive = sensitive

    def add_tracer(self, callback):
        raise NotImplementedError("Required to trace setting")

    def add_on_edit_end_callback_nosensitive(self, callback):
        raise NotImplementedError("Required to trace editing done")

    def add_on_edit_end_callback(self, callback):
        if self.sensitive:
            self.add_tracer(callback)
        else:
            self.add_on_edit_end_callback_nosensitive(callback)

    def build_setting(self, frame):
        raise NotImplementedError("Required to use setting")

    def set_value(self, value):
        raise NotImplementedError("Required to write value of setting")

    def get_value(self):
        raise NotImplementedError("Required to read value of setting")

    def die(self, action):
        raise SettingFormatError(self.setting_key, action)

    def reset(self):
        self.set_value(self.initial_value)

    def set_dict_value(self, out_dict):
        out_dict[self.setting_key] = self.get_value()

    def get_dict_value(self, in_dict):
        if self.setting_key in in_dict.keys():
            self.set_value(in_dict[self.setting_key])

class CallbackFocusOutBind(Setting):
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self._callbacks = []

    def bind_focus(self, field):
        field.bind("<FocusOut>", self.on_focus_out)

    def on_focus_out(self, *args):
        for callback in self._callbacks:
            callback()

    def add_on_edit_end_callback_nosensitive(self, callback):
        self._callbacks.append(callback)

class EntryValue(CallbackFocusOutBind):
    def __init__(self, master, setting_key, initial_value, dtype=str, sensitive=False):
        super().__init__(master, setting_key, initial_value, sensitive=sensitive)
        self.dtype = dtype

    def add_tracer(self, callback):
        self.entryvar.trace("w",callback)

    def build_setting(self, frame):
        self.entryvar = tk.StringVar(self)
        self.entryvar.set(str(self.initial_value))
        entry = EntryWithEnterKey(frame, textvariable=self.entryvar)
        entry.pack(fill=tk.BOTH, expand=True)
        self.bind_focus(entry)


    def get_value(self):
        val = self.entryvar.get()
        try:
            res = self.dtype(val)
            return res
        except ValueError:
            self.die("reading")

    def set_value(self, value):
        self.entryvar.set(str(value))


class CheckboxValue(Setting):
    def __init__(self, master, setting_key, initial_value, sensitive=False):
        super(CheckboxValue, self).__init__(master, setting_key, initial_value,sensitive=sensitive)

    def add_tracer(self, callback):
        self.entryvar.trace("w",callback)

    def build_setting(self, frame):
        self.entryvar = tk.IntVar(self)
        tk.Checkbutton(frame, text="", variable=self.entryvar).pack(fill=tk.BOTH, expand=True)

    def get_value(self):
        return self.entryvar.get() != 0

    def set_value(self, value):
        self.entryvar.set(int(value))

    def add_on_edit_end_callback_nosensitive(self, callback):
        self.entryvar.trace("w", callback)


class RangeDoubleValue( Validatable, CallbackFocusOutBind):
    def __init__(self, master, setting_key, initial_value, start, end, step=0.01, fmt="%.2f", sensitive=False):
        self.start = start
        self.end = end
        self.step = step
        self.fmt = fmt
        Validatable.__init__(self, float)
        CallbackFocusOutBind.__init__(self, master, setting_key, initial_value,sensitive=sensitive)

    def add_tracer(self, callback):
        self.entryvar.trace("w", callback)

    def build_setting(self, frame):
        self.entryvar = tk.StringVar(self)
        self.entry_field = SpinboxWithEnterKey(frame, from_=self.start, to=self.end, increment=self.step, format=self.fmt,
                                       wrap=True, textvariable=self.entryvar)
        self.entry_field.pack(fill=tk.BOTH, expand=True)
        self.connect_validator(self.entryvar)
        self.bind_focus(self.entry_field)

    def get_value(self):
        strval = self.entry_field.get()
        if strval:
            try:
                floatval = float(strval)
                if floatval > self.end:
                    self.entry_field.set(str(self.end))
                    return self.end
                elif floatval < self.start:
                    self.entry_field.set(str(self.start))
                    return self.start
                else:
                    return floatval
            except:
                return self.initial_value
        else:
            return self.initial_value

    def set_value(self, value):
        self.entry_field.set(str(value))
        self.old_value = str(value)


class IntValue(Validatable, CallbackFocusOutBind):
    def __init__(self, master, setting_key, initial_value, sensitive=False):
        Validatable.__init__(self, int)
        CallbackFocusOutBind.__init__(self, master, setting_key, initial_value, sensitive=sensitive)

    def add_tracer(self, callback):
        self.entryvar.trace("w", callback)

    def build_setting(self, frame):
        self.entryvar = tk.StringVar(self)
        self.entry_field = EntryWithEnterKey(frame, textvariable=self.entryvar)
        self.entry_field.pack(fill=tk.BOTH, expand=True)
        self.connect_validator(self.entryvar)
        self.bind_focus(self.entry_field)


    def get_value(self):
        strval = self.entryvar.get()
        if strval:
            try:
                intval = int(strval)
                return intval
            except ValueError:
                return self.initial_value
        else:
            return self.initial_value

    def set_value(self, value):
        self.entryvar.set(str(value))
        self.old_value = self.entryvar.get()


class DoubleValue(Validatable, CallbackFocusOutBind):
    def __init__(self, master, setting_key, initial_value, sensitive=False):
        Validatable.__init__(self, float)
        CallbackFocusOutBind.__init__(self, master, setting_key, initial_value, sensitive=sensitive)

    def add_tracer(self, callback):
        self.entryvar.trace("w", callback)


    def build_setting(self, frame):
        self.entryvar = tk.StringVar(self)
        self.entry_field = EntryWithEnterKey(frame, textvariable=self.entryvar)
        self.entry_field.pack(fill=tk.BOTH, expand=True)
        self.connect_validator(self.entryvar)
        self.bind_focus(self.entry_field)

    def get_value(self):
        strval = self.entryvar.get()
        if strval:
            try:
                floatval = float(strval)
                return floatval
            except ValueError:
                return self.initial_value
        else:
            return self.initial_value

    def set_value(self, value):
        self.entryvar.set(str(value))
        self.old_value = self.entryvar.get()


class RangeIntValue(Validatable, CallbackFocusOutBind):
    def __init__(self, master, setting_key, initial_value, start, end, sensitive=False):
        self.start = start
        self.end = end
        Validatable.__init__(self, int)
        CallbackFocusOutBind.__init__(self, master, setting_key, initial_value, sensitive=sensitive)

    def add_tracer(self, callback):
        self.entryvar.trace("w", callback)

    def build_setting(self, frame):
        self.entryvar = tk.StringVar(self)
        self.entry_field = SpinboxWithEnterKey(frame, from_=self.start, to=self.end,
                                       wrap=True, textvariable=self.entryvar)
        self.entry_field.pack(fill=tk.BOTH, expand=True)
        self.connect_validator(self.entryvar)
        self.bind_focus(self.entry_field)

    def set_limits(self, start, end):
        self.start = start
        self.end = end
        current_value = self.get_value()
        self.entry_field.config(from_=start, to=end)
        if current_value < start:
            self.set_value(start)
        elif current_value > end:
            self.set_value(end)


    def get_value(self):
        strval = self.entry_field.get()
        if strval:
            try:
                intval = int(strval)
                if intval>self.end:
                    self.entry_field.set(str(self.end))
                    return self.end
                elif intval<self.start:
                    self.entry_field.set(str(self.start))
                    return self.start
                else:
                    return intval
            except ValueError:
                return self.initial_value
        else:
            return self.initial_value

    def set_value(self, value):
        self.entry_field.set(str(value))
        self.old_value = self.entry_field.get()


class SliderRangeDoubleValue(Setting):
    def __init__(self, master, setting_key, initial_value, start, end, fmt="{:.2f}", sensitive=False):
        self.start = start
        self.end = end
        self.fmt = fmt
        self.tracing = dict()
        super(SliderRangeDoubleValue, self).__init__(master, setting_key, initial_value,sensitive=sensitive)

    def build_setting(self, frame):
        self.srcvar = tk.DoubleVar(self)
        self.srcvar.trace("w", self.propagate)
        self.displayvar = tk.StringVar(self)
        self.entry_field = ttk.Scale(frame, from_=self.start, to=self.end, orient=tk.HORIZONTAL, variable=self.srcvar)
        self.entry_field.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(frame, textvariable=self.displayvar, width=5).pack(side=tk.LEFT,fill=tk.BOTH)

    def propagate(self,*args):
        self.displayvar.set(self.fmt.format(self.srcvar.get()))

    def get_value(self):
        return self.entry_field.get()

    def set_value(self, value):
        self.entry_field.set(value)

class ComboboxValue(Setting):
    def __init__(self, master, setting_key, initial_value, options, sensitive=False):
        initial_value = options[0]
        self.listbox_options = options
        super(ComboboxValue, self).__init__(master, setting_key, initial_value, sensitive=sensitive)

    def build_setting(self, frame):
        self.combobox_variable = tk.StringVar(frame)
        self.combobox = ttk.Combobox(frame, state="readonly", values=self.listbox_options, textvariable=self.combobox_variable)
        self.combobox.pack(fill=tk.BOTH, expand=True)

    def get_value(self):
        return self.combobox.get()

    def set_value(self, value):
        self.combobox.set(value)

    def add_tracer(self, callback):
        self.combobox_variable.trace("w", callback)

    def add_on_edit_end_callback_nosensitive(self, callback):
        self.combobox.bind("<FocusOut>", callback)

class SettingMenu(ScrollableFrame):
    def __init__(self, master, autocommit=False, *args, **kwargs):
        super(SettingMenu, self).__init__(master, *args, **kwargs)
        self.user_settings = []
        self.columnconfigure(0,weight=1)
        self.separator_count = 0
        self.on_change_callback = None
        self.autocommiting = autocommit
        if not autocommit:
            self.commit_btn = ttk.Button(self, text="ОК", command=self.on_commit)
            self.commit_btn.grid(row=2, column=0, sticky="ew", columnspan=2)
        self.commit_action = None
        #self.change_notify = dict()
        self._notify_en = True
        self.change_schedule = list()
        self.change_callbacks = dict()

    def notify_enable(self):
        self._notify_en = True

    def notify_disable(self):
        self._notify_en = False


    def autocommit_tracer(self, *args):
        self.on_commit()

    def notify_change(self, key):
        if self._notify_en:
            self.change_schedule.append(key)
        # self.change_notify[key] = True

    def add_tracer(self, key, callback):
        for s in self.user_settings:
            s: Setting
            if s.setting_key == key:
                def caller(*args):
                    self.notify_change(key)
                s.add_tracer(caller)
                # self.change_notify[key] = False
                self.change_callbacks[key] = callback
                break

    def get_new_row(self):
        return len(self.user_settings)+self.separator_count

    def on_commit(self):
        if self.commit_action:
            self.commit_action()

    def add_setting(self, setting_type, setting_key, display_name, initial_value, **kwargs):
        newsetting = setting_type(self.contents, setting_key, initial_value, **kwargs)
        newrow = self.get_new_row()
        self.user_settings.append(newsetting)
        ttk.Label(self.contents,text=display_name).grid(row=newrow, column=0, sticky="ew")
        newsetting.grid(row=newrow, column=1, sticky="ew")
        if self.autocommiting:
            newsetting.add_on_edit_end_callback(self.autocommit_tracer)
        return newsetting

    def add_separator(self,display_name):
        newrow = self.get_new_row()
        ttk.Label(self.contents, text=display_name, anchor="center", font='TkDefaultFont 10 bold').\
            grid(row=newrow, column=0, sticky="ew", columnspan=2)
        self.separator_count += 1

    def lookup_setting(self, key):
        for s in self.user_settings:
            s: Setting
            if s.setting_key == key:
                return s

    def push_settings_dict(self, out_settings_dict: dict):
        '''
        Changes dict according to settings in frame
        :param out_settings_dict:
        :return:
        '''
        for s in self.user_settings:
            s: Setting
            s.set_dict_value(out_settings_dict)

        self._notify_en = False
        while self.change_schedule:
            k = self.change_schedule.pop(0)
            self.change_callbacks[k]()
        self._notify_en = True

        # for k in self.change_notify.keys():
        #     if self.change_notify[k]:
        #         self.change_callbacks[k]()
        #         self.change_notify[k] = False


    def pull_settings_dict(self,in_settings_dict: dict, custom_keys = None):
        '''
        Changes settings in frame according to dict
        :param in_settings_dict:
        :param custom_keys:
        :return:
        '''
        for s in self.user_settings:
            s:Setting
            if custom_keys is not None:
                if s.setting_key in custom_keys:
                    s.get_dict_value(in_settings_dict)
            else:
                s.get_dict_value(in_settings_dict)
