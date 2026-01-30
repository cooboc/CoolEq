cmake_minimum_required(VERSION 3.16)
project(CoolEq C CXX)

# ==============================================================================
# Options and Configuration
# ==============================================================================
option(ENABLE_COMPILATION_DB "Generate compile_commands.json" ON)

if(ENABLE_COMPILATION_DB)
    set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
endif()

# Default Board Selection (User can override with -DARDUINO_BOARD=...)
# Example: esp32:esp32:esp32 for generic ESP32
# Example: stm32:stm32:GenF4 for STM32
if(NOT DEFINED ARDUINO_BOARD)
    set(ARDUINO_BOARD "esp32:esp32:esp32")
    message(STATUS "Defaulting to board: ${ARDUINO_BOARD}")
endif()

# ==============================================================================
# Arduino CMake Toolchain
# ==============================================================================
# This uses the standard Arduino CMake Toolchain to handle the build process,
# dependencies, and board SDKs.
include(FetchContent)
FetchContent_Declare(
    Arduino-CMake-Toolchain
    GIT_REPOSITORY https://github.com/PLEN-Project/arduino-cmake-toolchain.git
    GIT_TAG        main
)
FetchContent_MakeAvailable(Arduino-CMake-Toolchain)

# ==============================================================================
# OnStepX Target
# ==============================================================================
set(ONSTEPX_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src/function/OnStepX)

# Check if Config.h is configured
if(NOT EXISTS "${ONSTEPX_DIR}/Config.h")
    message(WARNING "Config.h not found in ${ONSTEPX_DIR}. Copying example config.")
    # You might want to copy a default config here or error out
endif()

# Recursively find all source files
# Note: OnStepX relies on preprocessor guards to exclude incompatible HALs,
# so we can add all sources and let the compiler/linker handle it.
file(GLOB_RECURSE ONSTEPX_SOURCES 
    "${ONSTEPX_DIR}/src/*.cpp"
    "${ONSTEPX_DIR}/src/*.c"
    "${ONSTEPX_DIR}/src/*.h"
    "${ONSTEPX_DIR}/src/*.hpp"
)

# Define the Arduino Sketch Target
arduino_compile_executable(CoolEq
    BOARD ${ARDUINO_BOARD}
    SKETCH ${ONSTEPX_DIR}/OnStepX.ino
    SRCS ${ONSTEPX_SOURCES}
)

# Include Directories
target_include_directories(CoolEq PRIVATE
    ${ONSTEPX_DIR}/src
    ${ONSTEPX_DIR} # For Config.h in the root of the sketch
)

# ==============================================================================
# Compilation Flags
# ==============================================================================
# Add any project-specific definitions here
# target_compile_definitions(CoolEq PRIVATE ...)

message(STATUS "Build configured for ${ARDUINO_BOARD}")
message(STATUS "Source dir: ${ONSTEPX_DIR}")
