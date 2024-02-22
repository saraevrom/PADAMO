#!/usr/bin/env python3
import os
import subprocess

import argparse

APP_NAME = "PADAMO"
parser = argparse.ArgumentParser()
parser.add_argument("platform_postfix", type=str)
parser.add_argument("--onefile", default=False, action="store_true")
parser.add_argument("--tgtdir", default="", type=str)

ADD_ARGS = []

if __name__=="__main__":
    in_args = parser.parse_args()
    files = os.listdir("node_lib/")
    files = ["node_lib."+item[:-3] for item in files if item.startswith("node_")]
    args = ["pyinstaller"]
    args.extend([f"--hidden-import={item}" for item in files])
    args.append("--hidden-import=onnxruntime-gpu")
    args.append("--hidden-import=onnxruntime")
    args.append("--hidden-import=PIL._tkinter_finder")
    if in_args.onefile:
        args.append("--onefile")
    else:
        args.append("--onedir")

    if in_args.tgtdir:
        args.append(f"--distpath {in_args.tgtdir}")
    if ADD_ARGS:
        args.extend(ADD_ARGS)
    EXEC_NAME = f"{APP_NAME}-{in_args.platform_postfix}"
    args.append(f"-n{EXEC_NAME}")
    args.append("main.py")
    subprocess.run(args)
