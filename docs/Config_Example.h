/* ---------------------------------------------------------------------------------------------------------------------------------
 * OnStepX Configuration Example
 * Generated for User Project
 * ---------------------------------------------------------------------------------------------------------------------------------
 */

// CONTROLLER ======================================================================================================================
#define HOST_NAME                "OnStepX_Ctrl" // Hostname for this device

// PINMAP ------------------------------------------------- 
#define PINMAP                        MaxESP4   // Using MaxESP4 board (ESP32 based)

// SERIAL PORT COMMAND CHANNELS --------------------- 
#define SERIAL_A_BAUD_DEFAULT        115200     // USB Serial
#define SERIAL_B_BAUD_DEFAULT        9600       // Auxiliary Serial

// MOUNT ===========================================================================================================================

// AXIS1 RA/AZM -------------------------------------------------------- 
#define AXIS1_DRIVER_MODEL            TMC2209   // TMC2209 UART Driver
#define AXIS1_STEPS_PER_DEGREE        12800     // Steps per degree (Example: 200 * 16 * 4 / 1)
#define AXIS1_REVERSE                 OFF       // Normal direction
#define AXIS1_LIMIT_MIN              -180       // Min Hour Angle
#define AXIS1_LIMIT_MAX               180       // Max Hour Angle

// AXIS2 DEC/ALT ------------------------------------------------------- 
#define AXIS2_DRIVER_MODEL            TMC2209   // TMC2209 UART Driver
#define AXIS2_STEPS_PER_DEGREE        12800     // Steps per degree
#define AXIS2_REVERSE                 OFF       // Normal direction
#define AXIS2_LIMIT_MIN               -90       // Min Declination
#define AXIS2_LIMIT_MAX                90       // Max Declination

// MOUNT TYPE -------------------------------------------------------- 
#define MOUNT_TYPE                    GEM       // German Equatorial Mount

// SLEWING BEHAVIOUR ------------------------------------------ 
#define SLEW_RATE_BASE_DESIRED        2.0       // Desired slew rate in deg/sec (Fast slewing)

// TIME AND LOCATION ---------------------------------------------- 
#define TIME_LOCATION_SOURCE          DS3231    // RTC module

// WIFI -----------------------------------------------------------
#define WIFI_ENABLED                  ON
#define WIFI_SSID                     "OnStepX_AP"
#define WIFI_PASSWORD                 "password"

// ---------------------------------------------------------------------------------------------------------------------------------
#define FileVersionConfig 6
#include "Extended.config.h"
