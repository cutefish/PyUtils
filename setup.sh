#!/bin/bash

PYUTILSHOME=`pwd`
BASHSCRIPT=$HOME/.bashrc

echo >> $BASHSCRIPT
echo "#Adding PyUtils to python path" >> $BASHSCRIPT
echo "export PYTHONPATH=\$PYTHONPATH:$PYUTILSHOME/lib" >> $BASHSCRIPT
echo "export PATH=\$PATH:$PYUTILSHOME/bin" >> $BASHSCRIPT
