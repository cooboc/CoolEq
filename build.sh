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

# Setup local tools environment
TOOLS_DIR="$(pwd)/tools"
mkdir -p "$TOOLS_DIR/bin"
export PATH="$TOOLS_DIR/bin:$PATH"

# Try to find bundled arduino-cli from user's IDE
IDE_CLI_PATH="/home/zhao/workspace/arduino-ide_2.3.6_Linux_64bit/resources/app/lib/backend/resources/arduino-cli"
if [ -f "$IDE_CLI_PATH" ]; then
    echo "Found bundled arduino-cli at $IDE_CLI_PATH"
    if [ -f "$TOOLS_DIR/bin/arduino-cli" ]; then
        # Check if it's the same or we should replace it
        # Just replace it to be safe and ensure we use the one that sees the cores
        rm "$TOOLS_DIR/bin/arduino-cli"
    fi
    echo "Linking bundled arduino-cli..."
    ln -s "$IDE_CLI_PATH" "$TOOLS_DIR/bin/arduino-cli"
    chmod +x "$TOOLS_DIR/bin/arduino-cli"
fi

# Check for existing Arduino data directory
if [ -d "$HOME/.arduino15" ]; then
    echo "Using existing Arduino data directory: $HOME/.arduino15"
    export ARDUINO_DIRECTORIES_DATA="$HOME/.arduino15"
    export ARDUINO_DIRECTORIES_DOWNLOADS="$HOME/.arduino15/staging"
else
    export ARDUINO_DIRECTORIES_DATA="$TOOLS_DIR/data"
    export ARDUINO_DIRECTORIES_DOWNLOADS="$TOOLS_DIR/downloads"
fi

export ARDUINO_DIRECTORIES_USER="$TOOLS_DIR/user"
export ARDUINO_CONFIG_FILE="$TOOLS_DIR/arduino-cli.yaml"

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
        return 1
    fi
    return 0
}

# 1. Install arduino-cli if missing
if ! check_command arduino-cli; then
    echo "arduino-cli not found. Installing locally to $TOOLS_DIR/bin..."
    mkdir -p "$TOOLS_DIR/bin"
    # Use curl to download the installation script
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR="$TOOLS_DIR/bin" sh
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install arduino-cli."
        exit 1
    fi
else
    echo "arduino-cli found at $(command -v arduino-cli)"
fi

# 2. Configure arduino-cli
echo "Configuring arduino-cli..."
if [ ! -f "$ARDUINO_CONFIG_FILE" ]; then
    mkdir -p "$TOOLS_DIR"
    arduino-cli config init --dest-dir "$TOOLS_DIR"
fi

# Ensure ESP32 URL is present
arduino-cli config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json

# Update index
echo "Updating core index..."
arduino-cli core update-index

# Install Core for the requested board
# Simple heuristic: check the vendor package from the FQBN
PACKAGE=$(echo "$BOARD" | cut -d':' -f1)
ARCH=$(echo "$BOARD" | cut -d':' -f2)
CORE="$PACKAGE:$ARCH"

# Determine CMake Board ID from FQBN
# FQBN format: Package:Arch:Board
# Toolchain expects: Arch.Board
if [[ "$BOARD" == *":"* ]]; then
    BOARD_ID=$(echo "$BOARD" | cut -d':' -f3)
    # If Board ID is empty (e.g. esp32:esp32), this logic might fail, but FQBN usually has 3 parts for board selection
    if [ -n "$BOARD_ID" ]; then
        CMAKE_BOARD="$ARCH.$BOARD_ID"
    else
        CMAKE_BOARD="$BOARD" # Fallback
    fi
else
    CMAKE_BOARD="$BOARD"
fi

echo "Ensuring core '$CORE' is installed..."
if arduino-cli core list | grep -q "$CORE"; then
    echo "Core '$CORE' is already installed. Skipping installation."
else
    arduino-cli core install "$CORE"
fi

# 3. Check Prerequisites (CMake)
echo "Checking prerequisites..."
if ! check_command cmake; then
    echo "Error: cmake could not be found. Please install it to proceed."
    exit 1
fi

# 4. Prepare Build Directory
if [ "$CLEAN_BUILD" = true ]; then
    echo "Cleaning build directory..."
    rm -rf "$BUILD_DIR"
fi

if [ ! -d "$BUILD_DIR" ]; then
    echo "Creating build directory '$BUILD_DIR'..."
    mkdir "$BUILD_DIR"
fi

# 5. Configure with CMake
echo "========================================================"
echo "Configuring for Board: $BOARD"
echo "========================================================"

cd "$BUILD_DIR" || exit

cmake .. \
    -DARDUINO_BOARD="$BOARD" \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DFETCHCONTENT_SOURCE_DIR_ARDUINO-CMAKE-TOOLCHAIN="$TOOLS_DIR/arduino-cmake-toolchain" \
    -DARDUINO_PACKAGE_PATH="$ARDUINO_DIRECTORIES_DATA"

if [ $? -ne 0 ]; then
    echo "Error: CMake configuration failed."
    exit 1
fi

# 6. Build
echo "========================================================"
echo "Starting Build..."
echo "========================================================"

# Determine number of cores for parallel build
if command -v nproc &> /dev/null; then
    JOBS=$(nproc)
else
    JOBS=2 # Default to 2 if nproc not available
fi

echo "Building with $JOBS parallel jobs..."
cmake --build . --parallel "$JOBS"

if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "Build Successful!"
    echo "Artifacts are located in: $(pwd)"
    echo "========================================================"
else
    echo "Error: Build failed."
    exit 1
fi
