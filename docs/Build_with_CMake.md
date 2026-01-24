# CoolEq Build Instructions (CMake)

This project supports building **OnStepX** using CMake, which allows for a standard C++ development workflow.

## Prerequisites

1.  **CMake** (3.16 or newer)
2.  **Arduino CLI** or **Arduino IDE** (installed and in your PATH)
3.  **Core Platforms** for your target board installed via Arduino CLI/IDE.

## Setup

1.  **Install Arduino CLI** (if not already installed):
    ```bash
    brew install arduino-cli  # macOS
    # or download from https://arduino.github.io/arduino-cli/
    ```

2.  **Install Core Platforms**:
    Depending on your target board (e.g., ESP32, STM32, AVR), install the necessary cores.
    ```bash
    # Update index
    arduino-cli core update-index
    
    # For ESP32
    arduino-cli config init
    arduino-cli config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
    arduino-cli core update-index
    arduino-cli core install esp32:esp32
    ```

## Building with CMake

1.  **Create a build directory**:
    ```bash
    mkdir build && cd build
    ```

2.  **Configure the project**:
    Specify your target board using the `ARDUINO_BOARD` variable. The format is `package:arch:board`.
    
    *Example for generic ESP32:*
    ```bash
    cmake .. -DARDUINO_BOARD="esp32:esp32:esp32"
    ```

    *Example for Mega2560:*
    ```bash
    cmake .. -DARDUINO_BOARD="arduino:avr:mega"
    ```

3.  **Build**:
    ```bash
    cmake --build .
    ```

4.  **Upload** (Optional):
    You can use `arduino-cli` directly to upload, or if the toolchain supports it (check `arduino-cmake-toolchain` docs).
    ```bash
    arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 --input-dir .
    ```

## Configuration

The main configuration for OnStepX is located in `src/function/OnStepX/Config.h`.
Ensure you have edited this file to match your hardware setup (Pinmaps, Drivers, etc.) before building.
