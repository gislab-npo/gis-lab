#!/bin/bash
# Download and compile latest development version of QGIS.

set -e


echo "This script will download latest QGIS source code and make install"
echo "Continue ? [ENTER to continue, CTRL-C to cancel]"
read


QGIS_REPO=https://github.com/qgis/QGIS.git

mkdir -p ~/apps

if [ ! -f ~/bin/gcc ]; then
    ln -s /usr/bin/ccache ~/bin/gcc
    ln -s /usr/bin/ccache ~/bin/g++
fi

if [ ! -d "/$HOME/Projects/qgis-dev" ]; then
    git clone $QGIS_REPO ~/Projects/qgis-dev

    mkdir -p ~/Projects/qgis-dev/build-master
    cd ~/Projects/qgis-dev/build-master
    cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_INSTALL_PREFIX=${HOME}/apps ..
else
    cd ~/Projects/qgis-dev/build-master
    git pull
fi

make && make install

echo  "Done. Run command '$ qgis-dev' to start QGIS"

# vim: set ts=8 sts=4 sw=4 et:
