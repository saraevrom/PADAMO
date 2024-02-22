import os
from padamo.appdata import USER_DATA_DIR


class AppWorkspace(object):
    SUBPATH = "common"

    def __init__(self):
        self.tgtdir = os.path.join(USER_DATA_DIR, self.SUBPATH)
        if not os.path.isdir(self.tgtdir):
            os.makedirs(self.tgtdir)
            self.populate()

    def __call__(self, local_path):
        return os.path.join(self.tgtdir,local_path)

    def populate(self):
        '''
        Create files inside new directory
        :return:
        '''
        pass
