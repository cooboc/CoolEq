#!/bin/bash

# ==============================================================================
# Common Environment Configuration for CoolEq (Linux)
# ==============================================================================

# Determine Project Root
if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# Paths
BUILD_DIR="$PROJECT_ROOT/build"
TOOLS_DIR="$PROJECT_ROOT/tools_linux"
ARDUINO_CLI="$TOOLS_DIR/bin/arduino-cli"

# Setup isolated environment variables for Arduino CLI
export ARDUINO_DIRECTORIES_DATA="$TOOLS_DIR/data"
export ARDUINO_DIRECTORIES_DOWNLOADS="$TOOLS_DIR/downloads"
export ARDUINO_DIRECTORIES_USER="$TOOLS_DIR/user"
export PATH="$TOOLS_DIR/bin:$PATH"

# Default Board
DEFAULT_BOARD="esp32:esp32:esp32"

# Helper: Install Arduino CLI if missing
install_arduino_cli() {
    if [ ! -f "$ARDUINO_CLI" ]; then
        echo "arduino-cli not found. Installing locally to $TOOLS_DIR/bin..."
        mkdir -p "$TOOLS_DIR/bin"
        if ! command -v curl &> /dev/null; then
            echo "Error: curl is required but not installed."
            exit 1
        fi
        curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR="$TOOLS_DIR/bin" sh
    fi
}

# Helper: Configure Arduino CLI
configure_arduino_cli() {
    if [ ! -f "$TOOLS_DIR/arduino-cli.yaml" ]; then
        echo "Initializing arduino-cli configuration..."
        "$ARDUINO_CLI" config init --dest-dir "$TOOLS_DIR"
        "$ARDUINO_CLI" config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
        echo "Updating core index..."
        "$ARDUINO_CLI" core update-index
    fi
}
