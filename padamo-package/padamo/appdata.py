import os
from appdirs import AppDirs
APPNAME = "data_viewer"
AUTHOR = "saraevrom"

DIRECTORIES = AppDirs(APPNAME, AUTHOR)
os.makedirs(DIRECTORIES.user_data_dir, exist_ok=True)


USER_DATA_DIR = DIRECTORIES.user_data_dir