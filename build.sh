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
# Force version 2.0.17 for compatibility
TARGET_VERSION="2.0.17"
INSTALLED_VERSION=$(arduino-cli core list | grep "$CORE" | awk '{print $2}')

# Check if the installed version is EXACTLY the target version
if [ "$INSTALLED_VERSION" == "$TARGET_VERSION" ]; then
    echo "Core '$CORE' version $TARGET_VERSION is already installed."
else
    echo "Installing Core '$CORE' version $TARGET_VERSION..."
    # Uninstall current if it exists and is not target? 
    # arduino-cli core install replaces it usually.
    arduino-cli core install "$CORE@$TARGET_VERSION"
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

# 5. Build with Arduino CLI (Direct Mode)
echo "========================================================"
echo "Compiling with Arduino CLI for Board: $BOARD"
echo "========================================================"

# Compile Sketch
# Assuming the sketch is at src/function/OnStepX/OnStepX.ino
SKETCH_PATH="$(pwd)/src/function/OnStepX/OnStepX.ino"
BUILD_PATH="$(pwd)/$BUILD_DIR"

if [ ! -f "$SKETCH_PATH" ]; then
    echo "Error: Sketch not found at $SKETCH_PATH"
    exit 1
fi

echo "Sketch: $SKETCH_PATH"
echo "Output: $BUILD_PATH"

# Ensure build directory exists
mkdir -p "$BUILD_PATH"

arduino-cli compile \
    --fqbn "$BOARD" \
    --build-path "$BUILD_PATH" \
    --build-property "compiler.cpp.extra_flags=-DSERIAL_B=Serial1" \
    --jobs 0 \
    --verbose \
    "$SKETCH_PATH"

if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "Build Successful!"
    echo "Artifacts are located in: $BUILD_PATH"
    echo "========================================================"
else
    echo "Error: Build failed."
    exit 1
fi

# Note: We are bypassing CMake for the actual build process to use the native CLI speed and stability.
# However, if you need compile_commands.json for IDE intellisense, you might still want a minimal CMake setup later.
