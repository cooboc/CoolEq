#!/bin/bash
set -e

# ==============================================================================
# Pure Linux Build Script for CoolEq (OnStepX)
# Usage: ./linux_build.sh [board_fqbn]
# Example: ./linux_build.sh esp32:esp32:esp32
# ==============================================================================

# Determine Project Root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common environment
if [ -f "$PROJECT_ROOT/linux_env.sh" ]; then
    source "$PROJECT_ROOT/linux_env.sh"
else
    echo "Error: linux_env.sh not found."
    exit 1
fi

BOARD="${1:-$DEFAULT_BOARD}"

echo "Using Project Root: $PROJECT_ROOT"
echo "Target Board: $BOARD"

# Check for basic dependencies
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required for ESP32 tools but not installed."
    exit 1
fi

# 1. Install & Configure Arduino CLI
install_arduino_cli
configure_arduino_cli

# 2. Install Core for the requested board
PACKAGE=$(echo "$BOARD" | cut -d':' -f1)
ARCH=$(echo "$BOARD" | cut -d':' -f2)
CORE="$PACKAGE:$ARCH"

# Check if core is installed
if ! "$ARDUINO_CLI" core list | grep -q "$CORE"; then
    echo "Installing Core '$CORE'..."
    "$ARDUINO_CLI" core install "$CORE"
else
    echo "Core '$CORE' is already installed."
fi

# 3. Compile
SKETCH_PATH="$PROJECT_ROOT/src/function/OnStepX/OnStepX.ino"

if [ ! -f "$SKETCH_PATH" ]; then
    echo "Error: Sketch not found at $SKETCH_PATH"
    exit 1
fi

echo "========================================================"
echo "Compiling with Arduino CLI..."
echo "Sketch: $SKETCH_PATH"
echo "Output: $BUILD_DIR"
echo "========================================================"

mkdir -p "$BUILD_DIR"

# Note: Added -g for debug symbols. Optimization levels might need adjustment for full debug experience (-Og), 
# but -g is safe for general builds.
"$ARDUINO_CLI" compile \
    --fqbn "$BOARD" \
    --build-path "$BUILD_DIR" \
    --build-property "compiler.cpp.extra_flags=-DSERIAL_B=Serial1 -g" \
    --warnings all \
    --verbose \
    "$SKETCH_PATH"

if [ $? -eq 0 ]; then
    echo "========================================================"
    echo "Build Successful!"
    echo "Artifacts are located in: $BUILD_DIR"
    echo "========================================================"
else
    echo "Error: Build failed."
    exit 1
fi
