#!/bin/bash
#
# build_deps.sh
# DicomToolsCpp
#
# Bootstraps external dependencies (GDCM, DCMTK, ITK, VTK) by cloning and building them into a local prefix for the project.
#
# Thales Matheus Mendonça Santos - November 2025

set -e

# Configuration
DEPS_DIR="$(pwd)/deps"
SRC_DIR="$DEPS_DIR/src"
INSTALL_DIR="$DEPS_DIR/install"
THREADS=$(sysctl -n hw.ncpu || echo 4)

mkdir -p "$SRC_DIR"
mkdir -p "$INSTALL_DIR"

echo "======================================================="
echo "  Dicom-Tools-cpp Dependency Builder"
echo "  Install Prefix: $INSTALL_DIR"
echo "  Building with $THREADS threads"
echo "======================================================="

# Check for CMake
if ! command -v cmake &> /dev/null; then
    echo "Error: cmake could not be found. Please install it (e.g., 'brew install cmake')."
    exit 1
fi

# --- GDCM ---
echo ">>> Processing GDCM..."
if [ ! -d "$INSTALL_DIR/lib/cmake/gdcm-3.0" ] && [ ! -d "$INSTALL_DIR/lib/gdcm-3.0" ]; then
    if [ ! -d "$SRC_DIR/GDCM" ]; then
        git clone --depth 1 --branch release-3.0.24 https://github.com/malaterre/GDCM.git "$SRC_DIR/GDCM"
    fi
    mkdir -p "$SRC_DIR/GDCM/build"
    cd "$SRC_DIR/GDCM/build"
    cmake -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
          -DCMAKE_BUILD_TYPE=Release \
          -DGDCM_BUILD_SHARED_LIBS=ON \
          -DGDCM_BUILD_APPLICATIONS=OFF \
          -DGDCM_BUILD_EXAMPLES=OFF \
          -DGDCM_BUILD_TESTING=OFF \
          ..
    make -j"$THREADS"
    make install
    cd ../../..
else
    echo "    GDCM already installed."
fi

# --- DCMTK ---
echo ">>> Processing DCMTK..."
if [ ! -d "$INSTALL_DIR/include/dcmtk" ]; then
    if [ ! -d "$SRC_DIR/dcmtk" ]; then
        git clone --depth 1 --branch DCMTK-3.6.8 https://github.com/DCMTK/dcmtk.git "$SRC_DIR/dcmtk"
    fi
    mkdir -p "$SRC_DIR/dcmtk/build"
    cd "$SRC_DIR/dcmtk/build"
    cmake -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
          -DCMAKE_BUILD_TYPE=Release \
          -DDCMTK_WITH_TIFF=OFF \
          -DDCMTK_WITH_PNG=OFF \
          -DDCMTK_WITH_XML=OFF \
          -DDCMTK_WITH_ZLIB=OFF \
          -DDCMTK_WITH_OPENSSL=OFF \
          -DDCMTK_WITH_ICONV=OFF \
          -DBUILD_APPS=OFF \
          ..
    make -j"$THREADS"
    make install
    cd ../../..
else
    echo "    DCMTK already installed."
fi

# --- ITK ---
echo ">>> Processing ITK (This may take a while)..."
if [ ! -d "$INSTALL_DIR/lib/cmake/ITK-5.3" ]; then
    if [ ! -d "$SRC_DIR/ITK" ]; then
        git clone --depth 1 --branch v5.3.0 https://github.com/InsightSoftwareConsortium/ITK.git "$SRC_DIR/ITK"
    fi
    mkdir -p "$SRC_DIR/ITK/build"
    cd "$SRC_DIR/ITK/build"
    cmake -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
          -DCMAKE_BUILD_TYPE=Release \
          -DBUILD_TESTING=OFF \
          -DBUILD_EXAMPLES=OFF \
          -DITK_BUILD_DEFAULT_MODULES=OFF \
          -DModule_ITKIOImageBase=ON \
          -DModule_ITKIONRRD=ON \
          -DModule_ITKIOGDCM=ON \
          -DModule_ITKSmoothing=ON \
          ..
    make -j"$THREADS"
    make install
    cd ../../..
else
    echo "    ITK already installed."
fi

# --- VTK ---
echo ">>> Processing VTK (This will take a VERY long time)..."
if [ ! -d "$INSTALL_DIR/lib/cmake/vtk-9.3" ]; then
    if [ ! -d "$SRC_DIR/VTK" ]; then
        git clone --depth 1 --branch v9.3.0 https://github.com/Kitware/VTK.git "$SRC_DIR/VTK"
    fi
    mkdir -p "$SRC_DIR/VTK/build"
    cd "$SRC_DIR/VTK/build"
    cmake -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
          -DCMAKE_BUILD_TYPE=Release \
          -DBUILD_TESTING=OFF \
          -DBUILD_EXAMPLES=OFF \
          -DVTK_BUILD_SCALED_SOA_ARRAYS=OFF \
          -DVTK_GROUP_ENABLE_Rendering=NO \
          -DVTK_GROUP_ENABLE_StandAlone=YES \
          -DVTK_GROUP_ENABLE_Imaging=YES \
          -DVTK_MODULE_ENABLE_VTK_IOImage=YES \
          ..
    make -j"$THREADS"
    make install
    cd ../../..
else
    echo "    VTK already installed."
fi

echo "======================================================="
echo "  All dependencies installed to:"
echo "  $INSTALL_DIR"
echo "======================================================="
