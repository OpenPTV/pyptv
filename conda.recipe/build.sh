#!/bin/bash

set -ev

git clone https://github.com/libcheck/check.git
cd check
cmake .
make
make install


cd ../openptv/liboptv
mkdir _build && cd _build
cmake ../ -DCMAKE_INSTALL_PREFIX=$PREFIX
make
make verify
make install
# cp ./src/liboptv.dylib ../../py_bind

cd ../../py_bind
python setup.py build_ext -I/usr/local/include -L/usr/local/lib
python setup.py install

export PATH=$PATH:/usr/local/lib
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib
# echo $LD_LIBRARY_PATH
# echo $PATH
# python -c "import sys; print sys.path"

cd test
nosetests -v

cd ../../../

python setup.py install --single-version-externally-managed --record=record.txt
