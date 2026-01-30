# OnStepX Telescope Controller 技术架构文档

## 1. 架构设计

```mermaid
graph TD
  A[用户界面] --> B[控制逻辑层]
  B --> C[硬件抽象层 (HAL)]
  C --> D[电机驱动接口]
  C --> E[编码器接口]
  C --> F[通信模块]

  subgraph "软件层"
    B
  end

  subgraph "硬件接口层"
    C
    D
    E
    F
  end

  subgraph "物理设备"
    G[电机 (Stepper/Servo/ODrive)]
    H[编码器]
    I[通信设备 (USB/WiFi/BT)]
  end

  D --> G
  E --> H
  F --> I
```

## 2. 技术描述

- **固件平台**: Arduino/ESP32/Teensy/STM32 平台
- **开发语言**: C++
- **配置工具**: PlatformIO / Arduino IDE
- **通信协议**: Serial, WiFi, Bluetooth, Ethernet
- **核心特性**: 支持Step/Dir, ODrive, Servo等多种驱动模式
- **依赖库**: 内部HAL层封装

## 3. 文件结构定义

基于OnStepX项目结构，文件组织结构如下：

```
OnStepX/
├── src/
│   ├── HAL/                    # 硬件抽象层 (Hardware Abstraction Layer)
│   ├── lib/                    # 核心库 (Axis, Encoder, WiFi, etc.)
│   ├── libApp/                 # 应用层库 (Commands, Weather, etc.)
│   ├── pinmaps/                # 硬件引脚映射
│   ├── telescope/              # 望远镜控制逻辑 (Mount, Focuser, Rotator)
│   ├── Config.h                # 主配置文件
│   └── OnStepX.ino             # 主程序入口
├── examples/                   # 示例配置和用法
├── cache/                      # 临时文件
└── docs/                       # 项目文档
```

## 4. 核心模块定义

### 4.1 坐标计算模块 (Telescope/Mount)
OnStepX 使用更先进的坐标变换和校准模型。

### 4.2 驱动控制模块 (lib/axis/motor)
支持多种驱动类型：
- `kTech`: 专用驱动
- `mksServo`: MKS伺服
- `oDrive`: ODrive驱动
- `servo`: 直流/步进伺服
- `stepDir`: 标准步进电机驱动 (TMC2130, TMC5160, TMC2209等)

### 4.3 硬件抽象层 (HAL)
支持多种MCU平台：
- `arduinoM0`
- `esp` (ESP32, ESP8266)
- `stm32`
- `teensy`

## 5. 数据模型

### 5.1 配置数据结构
OnStepX的配置主要通过 `Config.h` 宏定义进行编译时配置，运行时参数存储在NV (Non-Volatile) 存储中。

## 6. Config.h 配置模板 (OnStepX)

```cpp
// Config.h - OnStepX 主配置文件
/* ---------------------------------------------------------------------------------------------------------------------------------
 * Configuration for OnStepX
 * ---------------------------------------------------------------------------------------------------------------------------------
 */
 
// CONTROLLER ======================================================================================================================
#define HOST_NAME                "OnStep" // Hostname for this device

// PINMAP ------------------------------------------------- 
#define PINMAP                        OFF // Choose from: MiniPCB, MaxESP4, FYSETC_E4, etc.

// SERIAL PORT COMMAND CHANNELS --------------------- 
#define SERIAL_A_BAUD_DEFAULT        9600 
#define SERIAL_B_BAUD_DEFAULT        9600 

// MOUNT ===========================================================================================================================
// AXIS1 RA/AZM -------------------------------------------------------- 
#define AXIS1_DRIVER_MODEL            OFF // Enter motor driver model
#define AXIS1_STEPS_PER_DEGREE      12800 // Steps per degree
#define AXIS1_REVERSE                 OFF // Reverse movement
#define AXIS1_LIMIT_MIN              -180 // Min Hour Angle/Azimuth
#define AXIS1_LIMIT_MAX               180 // Max Hour Angle/Azimuth

// AXIS2 DEC/ALT ------------------------------------------------------- 
#define AXIS2_DRIVER_MODEL            OFF // Enter motor driver model
#define AXIS2_STEPS_PER_DEGREE      12800 // Steps per degree
#define AXIS2_REVERSE                 OFF // Reverse movement
#define AXIS2_LIMIT_MIN               -90 // Min Declination/Altitude
#define AXIS2_LIMIT_MAX                90 // Max Declination/Altitude

// MOUNT TYPE -------------------------------------------------------- 
#define MOUNT_TYPE                    GEM // GEM, ALTAZM, FORK, etc.

// SLEWING BEHAVIOUR ------------------------------------------ 
#define SLEW_RATE_BASE_DESIRED        1.0 // Desired slew rate in deg/sec

// TIME AND LOCATION ---------------------------------------------- 
#define TIME_LOCATION_SOURCE          OFF // DS3231, GPS, etc.

// ... 更多配置请参考 src/function/OnStepX/Config.h
```

## 7. 通信协议定义

### 7.1 串行命令格式
兼容LX200协议及OnStep扩展命令。
```
命令格式: :CCCSSSS# 
示例: :Gr# (Get RA), :Sd# (Set Dec)
```

## 8. 测试架构

OnStepX 包含针对各个模块的测试代码，建议在 `test/` 目录下组织针对 HAL 和核心算法的单元测试。