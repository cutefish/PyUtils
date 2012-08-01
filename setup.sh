#!/bin/bash

PYUTILSHOME=`pwd`
PARENT="$(dirname "$PYUTILSHOME")"
BASHSCRIPT=$HOME/.bashrc

echo >> $BASHSCRIPT
echo "#Adding PyUtils to python path" >> $BASHSCRIPT
echo "export PYTHONPATH=\$PYTHONPATH:$PARENT" >> $BASHSCRIPT
