# AXIS1 或 AXIS2 缺失的后果调查

当 `AXIS1` 或 `AXIS2` 在配置中被设置为 `OFF`（或因配置错误导致缺失）时，OnStepX 系统会产生以下后果：

## 1. 核心后果：望远镜功能完全禁用 (Software Feature Disabled)

这是最直接且严重的后果。OnStepX 的设计架构强制要求赤道仪或经纬仪必须同时具备两个主轴（RA/Dec 或 Az/Alt）才能作为“望远镜”工作。

*   **机制**: 
    在 `src/function/OnStepX/src/Common.h` 中，宏 `MOUNT_PRESENT` 的定义依赖于两个轴同时存在：
    ```cpp
    #if AXIS1_DRIVER_MODEL != OFF && AXIS2_DRIVER_MODEL != OFF
      #define MOUNT_PRESENT
    #endif
    ```

*   **结果**:
    *   如果 `AXIS1` 或 `AXIS2` 任意一个为 `OFF`，`MOUNT_PRESENT` 将**不会被定义**。
    *   **代码剔除**: `src/function/OnStepX/src/telescope/mount/Mount.h` 中的 `Mount` 类和全局 `mount` 对象会被预处理器完全剔除。
    *   **功能失效**: 所有望远镜核心功能（跟踪 Tracking、自动寻星 GoTo、导星 Guiding、子午线翻转等）将**彻底不可用**。
    *   **角色转变**: 固件实际上变成了一个纯粹的辅助设备控制器（如仅用于控制电动调焦器 Focuser 或旋转器 Rotator，如果它们存在的话）。

## 2. 硬件引脚的副作用 (Hardware Side Effects)

即使望远镜功能被禁用，固件在启动时仍可能操作部分硬件引脚，这取决于 `PINMAP` 的定义。

*   **使能引脚 (Enable Pins)**:
    在 `src/function/OnStepX/src/telescope/Telescope.cpp` 的构造函数中，**无论 `MOUNT_PRESENT` 是否定义**，只要引脚号在 Pinmap 中有效，系统都会初始化使能引脚：
    ```cpp
    if (AXIS1_ENABLE_PIN >= 0 ...) { pinMode(AXIS1_ENABLE_PIN, OUTPUT); ... }
    ```
    **后果**: 即使你关闭了 AXIS1 的逻辑功能，如果 Pinmap 里定义了它的 Enable 引脚，电机驱动器仍可能在系统上电时被使能（产生锁定力矩/发热）或被禁用（无力矩）。

*   **步进/方向引脚 (Step/Dir Pins)**:
    这些引脚的初始化受 `AXISx_STEP_DIR_PRESENT` 宏保护。如果驱动模型设为 `OFF`，该宏不定义，因此步进和方向引脚**不会**被初始化为输出模式，处于高阻态或浮空状态。

## 3. 运行时缺失 (Runtime Failure)

如果配置中两个轴都开启（`AXISx_DRIVER_MODEL` 不是 `OFF`），但在运行时检测不到硬件（例如 TMC 驱动器 UART 通信失败）：

*   **初始化报错**: `Mount::init()` 会检测驱动初始化返回值。如果 `axis1.init()` 返回 false，系统将设置 `initError.driver = true`。
*   **日志记录**: 串口会输出错误信息，例如 `ERR: Mount::init(), no motion controller for Axis1!`。
*   **状态指示**: 状态 LED 会闪烁报错（通常是错误代码 4，代表驱动错误）。
*   **功能受限**: 虽然 `mount` 对象存在，但由于驱动初始化失败，系统会禁止电机使能，导致整个望远镜系统无法运动。

## 4. 特殊场景：仅连接电机但缺失 UART 通信 (TMC2209 Standalone 风险)

如果在配置中选择了 TMC2209 驱动（`AXIS1_DRIVER_MODEL = TMC2209`），但物理上**仅连接了电机线和步进/方向线**，而**没有连接 UART 通信线**，系统将面临以下风险：

### 4.1 假性“初始化成功” (False Positive)
*   **现象**: `init()` 函数默认**不检查** UART 通信是否成功（除非开启 `MOTOR_DRIVER_DETECT`）。
*   **后果**: 系统会误认为驱动器工作正常，无任何报错，APP 显示连接成功。

### 4.2 电流失控风险 (Current Control Failure)
*   **待机状态 (Safe)**: 
    *   上电默认状态下，MCU 将 `ENABLE_PIN` 初始化为 **HIGH**（TMC2209 为低电平有效）。
    *   只要不进行任何操作（不开启跟踪、不按方向键），驱动器处于**禁用状态**，电机无电流，是安全的。
*   **工作状态 (Dangerous)**:
    *   一旦开启跟踪或移动望远镜，MCU 拉低 `ENABLE_PIN` 唤醒驱动器。
    *   由于 UART 缺失，驱动器无法接收软件设定的电流值（RMS Current）。
    *   驱动器回退到 **独立模式 (Standalone Mode)**，电流大小完全由驱动板上的 **物理旋钮 (VREF)** 决定。
    *   **严重后果**: 如果 VREF 默认值很高，电机可能瞬间过热甚至烧毁；如果过低，则无力矩。

### 4.3 运动参数错乱 (Motion Parameter Mismatch)
*   **细分错误**: 驱动器无法读取软件设定的细分（如 64 微步），而是根据物理引脚 `MS1/MS2` 决定（通常默认为 8 或 16 细分）。这将导致望远镜移动速度和指向精度完全错误。
*   **功能缺失**: 静音模式 (StealthChop)、防堵转等高级功能全部失效。

**建议**: 如果不打算使用 UART 通信，请务必在 `Config.h` 中将驱动模型改为 `A4988` 或 `LV8729`，并手动调整 VREF 和细分跳线。

## 5. AXIS3-9 的作用与配置关系

除了作为望远镜主轴的 `AXIS1` 和 `AXIS2`，OnStepX 还支持多达 7 个额外的轴（AXIS3 到 AXIS9），它们被用于特定的辅助功能。这些轴的开启与否直接决定了相关功能模块是否会被编译进固件。

### 5.1 旋转器 (Rotator) - AXIS3
*   **关联宏**: `ROTATOR_PRESENT`
*   **触发条件**: 
    在 `Common.h` 中定义：
    ```cpp
    #if AXIS3_DRIVER_MODEL != OFF
      #define ROTATOR_PRESENT
    #endif
    ```
*   **功能**: 
    *   当 `AXIS3` 开启时，`Rotator` 类及其全局对象 `rotator` 会被启用。
    *   该轴专门用于控制相机的场旋转器（Field Rotator），支持消场旋（Derotation）功能。
    *   如果 `MOUNT_PRESENT` 同时存在，旋转器可以根据望远镜的指向计算视场旋转速率并自动补偿。

### 5.2 调焦器 (Focuser) - AXIS4 到 AXIS9
*   **关联宏**: `FOCUSER_PRESENT`
*   **触发条件**:
    在 `Common.h` 中，只要 **AXIS4 到 AXIS9 中任意一个** 被开启，调焦器功能就会被激活：
    ```cpp
    #if AXIS4_DRIVER_MODEL != OFF || AXIS5_DRIVER_MODEL != OFF || ... || AXIS9_DRIVER_MODEL != OFF
      #define FOCUSER_PRESENT
    #endif
    ```
*   **多调焦器支持**:
    OnStepX 支持多个调焦器（Focuser 1 到 Focuser 6），它们分别对应硬件轴 AXIS4 到 AXIS9。
    *   `AXIS4` -> Focuser 1
    *   `AXIS5` -> Focuser 2
    *   ...
    *   `AXIS9` -> Focuser 6
*   **最大数量限制**:
    在 `src/telescope/focuser/local/Focuser.h` 中，宏 `FOCUSER_MAX` 会根据开启的最高轴号自动计算支持的调焦器最大数量。例如，如果只开启了 `AXIS4` 和 `AXIS6`，系统会认为最大支持到 Focuser 3（尽管中间的 Focuser 2 可能未配置，这取决于具体实现逻辑，通常是按顺序填充）。

### 5.3 独立性
*   **独立运行**: 即使 `AXIS1/2` 为 `OFF`（即 `MOUNT_PRESENT` 未定义），`ROTATOR_PRESENT` 和 `FOCUSER_PRESENT` 仍然可以独立存在。这意味着你可以利用 OnStepX 制作一个**独立的电动调焦控制器**或**独立的场旋转控制器**，而不需要连接赤道仪部分。
*   **联动性**: 如果 `MOUNT_PRESENT` 存在，旋转器和调焦器可以获得望远镜的状态信息（如温度补偿、指向位置等）来增强功能。
