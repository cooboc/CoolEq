#!/bin/bash

# ==============================================================================
# Pure Linux Debug Helper for CoolEq (OnStepX)
# Usage: ./linux_debug.sh [elf_path]
# Example: ./linux_debug.sh build/OnStepX.ino.elf
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

# Find ELF file
ELF_FILE="${1:-$BUILD_DIR/OnStepX.ino.elf}"

if [ ! -f "$ELF_FILE" ]; then
    echo "Error: ELF file not found at $ELF_FILE"
    echo "Please run ./linux_build.sh first."
    exit 1
fi

echo "Debugging Target: $ELF_FILE"

# Find Installed Tools (OpenOCD and GDB)
# We look into the tools folder managed by arduino-cli
# Typical path: tools_linux/data/packages/esp32/tools/openocd-esp32/<ver>/bin/openocd

ESP32_TOOLS_DIR="$TOOLS_DIR/data/packages/esp32/tools"

# Find OpenOCD
OPENOCD_BIN=$(find "$ESP32_TOOLS_DIR" -name "openocd" -type f | grep "openocd-esp32" | head -n 1)
OPENOCD_SCRIPTS=$(dirname "$(dirname "$OPENOCD_BIN")")/share/openocd/scripts

if [ -z "$OPENOCD_BIN" ]; then
    echo "Error: OpenOCD for ESP32 not found. Have you run ./linux_build.sh?"
    exit 1
fi

# Find GDB
# Typical path: tools_linux/data/packages/esp32/tools/xtensa-esp32-elf-gcc/<ver>/bin/xtensa-esp32-elf-gdb
GDB_BIN=$(find "$ESP32_TOOLS_DIR" -name "xtensa-esp32-elf-gdb" -type f | head -n 1)

if [ -z "$GDB_BIN" ]; then
    echo "Error: GDB (xtensa-esp32-elf-gdb) not found."
    exit 1
fi

echo "Found OpenOCD: $OPENOCD_BIN"
echo "Found GDB: $GDB_BIN"

# Debug Configuration
# Default to ESP-Prog (ftdi/esp32_devkitj_v1.cfg) and ESP32 target
# User can override these by setting env vars before running script
INTERFACE_CFG="${OPENOCD_INTERFACE:-interface/ftdi/esp32_devkitj_v1.cfg}"
TARGET_CFG="${OPENOCD_TARGET:-target/esp32.cfg}"

echo "--------------------------------------------------------"
echo "Starting Debug Session"
echo "Interface: $INTERFACE_CFG"
echo "Target:    $TARGET_CFG"
echo "--------------------------------------------------------"
echo "To change interface, run: export OPENOCD_INTERFACE=interface/..."
echo "To change target, run:    export OPENOCD_TARGET=target/..."
echo "--------------------------------------------------------"

# Launch OpenOCD in background
echo "Launching OpenOCD..."
"$OPENOCD_BIN" -s "$OPENOCD_SCRIPTS" -f "$INTERFACE_CFG" -f "$TARGET_CFG" &
OPENOCD_PID=$!

# Trap to kill OpenOCD on exit
cleanup() {
    echo "Stopping OpenOCD (PID $OPENOCD_PID)..."
    kill "$OPENOCD_PID"
}
trap cleanup EXIT

# Wait a bit for OpenOCD to initialize
sleep 2

# Launch GDB
echo "Launching GDB..."
"$GDB_BIN" -ex "target remote :3333" \
           -ex "mon reset halt" \
           -ex "flushregs" \
           -ex "thb app_main" \
           -ex "c" \
           "$ELF_FILE"

# GDB exit will trigger cleanup
