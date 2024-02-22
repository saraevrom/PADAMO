from .application import Application
import padamo.node_lib
import padamo.__main__
# See PyCharm help at https://www.jetbrains.com/help/pycharm/

def run():
    root = Application()
    root.mainloop()
