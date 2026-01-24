#!/bin/bash

# ==============================================================================
# CoolEq (OnStepX) Build Script
# Usage: ./build.sh [board_fqbn] [clean]
# Example: ./build.sh esp32:esp32:esp32
# ==============================================================================

# Default Configuration
DEFAULT_BOARD="esp32:esp32:esp32"
BUILD_DIR="build"
BOARD="$DEFAULT_BOARD"
CLEAN_BUILD=false

# Parse arguments
for arg in "$@"; do
    if [ "$arg" == "clean" ]; then
        CLEAN_BUILD=true
    else
        BOARD="$arg"
    fi
done

# Helper function to check for commands
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: '$1' could not be found. Please install it to proceed."
        exit 1
    fi
}

# 1. Check Prerequisites
echo "Checking prerequisites..."
check_command cmake
check_command arduino-cli

# 2. Prepare Build Directory
if [ "$CLEAN_BUILD" = true ]; then
    echo "Cleaning build directory..."
    rm -rf "$BUILD_DIR"
fi

if [ ! -d "$BUILD_DIR" ]; then
    echo "Creating build directory '$BUILD_DIR'..."
    mkdir "$BUILD_DIR"
fi

# 3. Configure with CMake
echo "========================================================"
echo "Configuring for Board: $BOARD"
echo "========================================================"

cd "$BUILD_DIR" || exit

cmake .. \
    -DARDUINO_BOARD="$BOARD" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

if [ $? -ne 0 ]; then
    echo "Error: CMake configuration failed."
    exit 1
fi

# 4. Build
echo "========================================================"
echo "Starting Build..."
echo "========================================================"

cmake --build .

if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "Build Successful!"
    echo "Artifacts are located in: $(pwd)"
    echo "========================================================"
else
    echo "Error: Build failed."
    exit 1
fi
