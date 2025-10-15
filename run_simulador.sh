#!/bin/bash
# Corrige o bug do Snap (libpthread.so) apenas para esta execução

export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libpthread.so.0
export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu
export GI_TYPELIB_PATH=/usr/lib/x86_64-linux-gnu/girepository-1.0
export PYTHONPATH=/usr/lib/python3/dist-packages

echo "Iniciando simulador TR1..."
python3 src/simulador.py
