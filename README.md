# CoolEq - OnStepX Telescope Controller Project

Welcome to the **CoolEq** project! This project is a customized telescope control system based on the [OnStepX](https://github.com/StarGazer1995/OnStepX) open-source controller.

## Project Overview

CoolEq aims to provide a high-performance, open-source telescope controller for astronomical mounts (GEM, Fork, Alt-Az). It leverages the advanced features of OnStepX, supporting a wide range of hardware including ESP32, Teensy, and STM32.

## Directory Structure

- **`src/function/OnStepX`**: The core OnStepX firmware (linked as a Git submodule).
- **`docs/`**: Project documentation, including:
  - `onstepx-prd.md`: Product Requirements Document.
  - `onstepx-technical-architecture.md`: Technical Architecture.
  - `project_development_plan.md`: Development roadmap.
  - `Config_Example.h`: A template configuration file for your setup.
- **`src/`**: Source code directory.
- **`test/`**: Unit and integration tests.
- **`cache/`**: Temporary build or cache files.
- **`examples/`**: Example configurations and scripts.

## Getting Started

### 1. Clone the Repository

```bash
git clone --recursive <repository-url>
# If you already cloned without --recursive:
git submodule update --init --recursive
```

### 2. Configure OnStepX

Copy the example configuration or use the default template:

```bash
cp docs/Config_Example.h src/function/OnStepX/Config.h
```
*Note: You will need to adjust `Config.h` to match your specific hardware pins and motor drivers.*

### 3. Build and Upload

This project is typically developed using **PlatformIO** or **Arduino IDE**.

- **PlatformIO**: Open the `src/function/OnStepX` folder in VS Code with the PlatformIO extension installed. Select your environment (e.g., `esp32`) and click "Build" / "Upload".

## Documentation

Please refer to the `docs/` folder for detailed architectural designs and development plans.

## License

This project is based on OnStepX (GPL-3.0 License). See the submodule for license details.
