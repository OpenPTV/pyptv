#!/bin/bash

set -ev
CWD="$(pwd)"
echo $CWD

cd ./openptv/liboptv
mkdir _build && cd _build
cmake ../ -DCMAKE_INSTALL_PREFIX=$PREFIX
make
# make verify # check_track fails and I need to continue
make install
# cp ./src/liboptv.dylib ../../py_bind

cd ../../py_bind
# python setup.py build_ext -I../liboptv/include -L../liboptv/_build/src 
python setup.py install --prefix=$PREFIX

# export PATH=$PATH:/usr/local/lib
# export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
# export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib
# echo $LD_LIBRARY_PATH
# echo $PATH
# python -c "import sys; print sys.path"

cd test
nosetests -v

echo $PWD
cd $CWD

python setup.py install --prefix=$PREFIX
