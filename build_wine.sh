#!/bin/bash

export WINEARCH=win64
export WINEPREFIX="$(pwd)/wineprefix"

PYVER="$(python -c 'import sys; print("{}.{}.{}".format(*sys.version_info[:3]))')"
PYLINK="https://www.python.org/ftp/python/${PYVER}/python-${PYVER}-amd64.exe"
PYDIST="python-${PYVER}-amd64.exe"
echo $PYLINK

if [ ! -f $PYDIST ]
then
  wget "$PYLINK"
fi

#if [ ! -d "$WINEPREFIX" ]
#then
#  wine cmd /C echo "TEST"
#fi

wine cmd /C "python --version" || wine $PYDIST

if [ ! -d "win64-venv" ]
then
  wine cmd /C "python -m venv win64-venv"
fi

wine cmd /C "build_win.bat"
