#!/bin/bash
source venv/bin/activate

# CUDNN_PATH=$(dirname $(python -c "import nvidia.cudnn;print(nvidia.cudnn.__file__)"))
# echo "CUDNN_PATH=${CUDNN_PATH}"
# export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$CUDNN_PATH/lib"

./padamo-package/main.py
