#!/bin/bash
APPIMAGE_DIR="./appimage"

PYTHON_APPIMAGE="https://github.com/niess/python-appimage/releases/download/python3.11/python3.11.6-cp311-cp311-manylinux2014_x86_64.AppImage"

PYTHON_NAME=`basename $PYTHON_APPIMAGE`


BIN_SUBPATH="usr/bin/python3.11"
OPT_SUBPATH="opt/python3.11"

#rm -rf "$APPIMAGE_DIR"
mkdir -pv "$APPIMAGE_DIR"

cd "$APPIMAGE_DIR" || exit
[ -f "$PYTHON_NAME" ] || wget $PYTHON_APPIMAGE -O "$PYTHON_NAME"
chmod +x "$PYTHON_NAME"

"./$PYTHON_NAME" --appimage-extract

PYTHON_DIR="${PYTHON_NAME//AppImage/AppDir}"
rm -rf "$PYTHON_DIR"

mv squashfs-root "$PYTHON_DIR"
ln -s "$PYTHON_DIR/AppRun" python

# Isolating environment
PATCH="$PYTHON_DIR/$BIN_SUBPATH"
cat "$PATCH" | sed '25s/"$@"$/-I "$@"/' | tee "$PATCH"

#installing app
./python -m pip install --upgrade  ../padamo-package || exit 1

#mv -v "$PYTHON_DIR/$OPT_SUBPATH/lib/libtbb*.so" "$PYTHON_DIR/usr/lib" || exit 1


#Making it run app
#cat $PATCH | sed '25s/"$@"$/-m padamo "$@"/' | tee $PATCH


#export LD_LIBRARY_PATH="${APPDIR}/opt/python3.11/lib:${APPDIR}/usr/lib:$LD_LIBRARY_PATH"
#echo "$LD_LIBRARY_PATH"


cat "$PATCH" | sed '25s|-I "$@"$|"$APPDIR/opt/python3.11/bin/padamo-run" "$@"|' | tee "$PATCH"

cat "$PATCH" | sed '23a export LD_LIBRARY_PATH="${APPDIR}/opt/python3.11/lib:${APPDIR}/usr/lib:$LD_LIBRARY_PATH"' | tee "$PATCH"



[ -f appimagetool-x86_64.AppImage ] || wget https://github.com/AppImage/AppImageKit/releases/download/continuous/\
appimagetool-x86_64.AppImage

chmod +x appimagetool-x86_64.AppImage

./appimagetool-x86_64.AppImage  -n \
"$PYTHON_DIR" \
PADAMO.AppImage
