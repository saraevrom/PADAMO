import tkinter as tk


def parse_int(x):
    try:
        return int(x)
    except ValueError:
        return 0


def parse_float(x):
    try:
        if x.endswith("e"):
            x0 = x[:-1]
        elif x.endswith("e-") or x.endswith("e+"):
            x0 = x[:-2]
        else:
            x0 = x
        return float(x0)
    except ValueError:
        return 0

class IntegerEntry(tk.Entry):
    def __init__(self, master, *args,**kwargs):
        super().__init__(master, *args,**kwargs)
        vcmd = (self.register(self.on_validate), '%P')
        self.configure(validatecommand=vcmd, validate="key")

    def on_validate(self, x):
        #print(P)
        try:
            int(x)
            return True
        except ValueError:
            if not x:
                return True
            if x == "-":
                return True
        return False



class FloatEntry(tk.Entry):
    def __init__(self, master, *args,**kwargs):
        super().__init__(master, *args,**kwargs)
        vcmd = (self.register(self.on_validate),'%P')
        self.configure(validatecommand=vcmd, validate="key")

    def on_validate(self,x):
        #print(P)
        try:
            if x.endswith("e"):
                x0 = x[:-1]
            elif x.endswith("e-") or x.endswith("e+"):
                x0 = x[:-2]
            else:
                x0 = x
            float(x0)
            return True
        except ValueError:
            if not x:
                return True
            if x == "-":
                return True
        return False

