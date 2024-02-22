#!/bin/bash

source venv/bin/activate

#NODE_LIB=$(python node_detect.py)
#echo $NODE_LIB
PLATFORM="$(uname -s)-$(uname -m)"
python build.py --onefile "${PLATFORM}"  --tgtdir="appimage/PADAMO-viewer.AppDir/"
cp -rv node_lib/ appimage/PADAMO-viewer.AppDir/  # Copy node_lib to appimage
(cd dist; appimagetool ../appimage/PADAMO-viewer.AppDir)
pyinstaller --hidden-import='PIL._tkinter_finder' $NODE_LIB --onefile main.py
