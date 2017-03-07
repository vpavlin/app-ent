#!/bin/bash
set -ex
pip install -r requirements.txt
pip install pyinstaller

# Due to the way that we dynamically load providers via import_module
# in atomicapp/plugin.py we have to specify explicitly the modules directly
# so pyinstaller can "see" them.
pyinstaller atomicapp.spec

mkdir -p bin
mv dist/main bin/atomicapp
echo "Binary created at bin/atomicapp"
