#!/bin/bash

mkdir -p ~/ptv-build
mkdir -p ~/ptv-build/wheels

cd ~/ptv-build
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install wheel
pip install numpy
pip install cython

# Install swig and python3
brew install python3
brew install swig@3
export PATH="/usr/local/opt/swig@3/bin:$PATH"   # Necessary to add swig3 to the path

# enable
 
# Enable 4.7.2 uses old Cython, which doesn't support Python 3.7. They have a fix on master, but it wasn't released yet
# Hopefully a future version of enable will include this fix and we'll just be able to use it
# For now, we check out the entire repository, use the 4.7.2 tag but patch the file from its own commit
git clone https://github.com/enthought/enable.git --branch 4.7.2

cd enable

# Get the correct kiva/_cython_speedups.cpp
git checkout 969c973 -- kiva/_cython_speedups.cpp

# On Mac OS Mojave, setup.py files for kiva pass the wrong arguments 
# to the linker. This was fixed by another commit, out of which we take only
# the relevant files
git checkout 77b2397 -- kiva/agg/setup.py
git checkout 77b2397 -- kiva/quartz/setup.py

python setup.py bdist_wheel

cp dist/* ~/ptv-build/wheels

# chaco
# Chaco has the same problem as enable, in the file downsample/_lttb.c
# We fix it the same way, by getting just this file from the commit that fixed the issue
cd ~/ptv-build
git clone https://github.com/enthought/chaco.git --branch 4.7.2

cd chaco
git checkout 14c5539 -- chaco/downsample/_lttb.c

python setup.py bdist_wheel
cp dist/* ~/ptv-build/wheels

# Traits
cd ~/ptv-build
git clone https://github.com/enthought/traits.git --branch 5.1.1 --single-branch --depth 1
cd traits
python setup.py bdist_wheel
cp dist/* ~/ptv-build/wheels

# Traits UI
cd ~/ptv-build
git clone https://github.com/enthought/traitsui.git --branch 6.1.1 --single-branch --depth 1
cd traitsui

# traitsui has just one wheel that is independent of the Python version, but we compile it build - just to make sure
python setup.py bdist_wheel
cp dist/* ~/ptv-build/wheels

