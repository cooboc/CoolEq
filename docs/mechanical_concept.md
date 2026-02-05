# CoolEq Mechanical Concept

Based on the [Project Plan](project-plan.md), here is the mechanical stacking and structural concept diagram.

## Mechanical Stack Diagram (Mermaid)

This diagram illustrates the physical hierarchy from the ground up to the payload.

```mermaid
graph BT
    subgraph Ground["Ground Support"]
        Tripod["Tripod / Pier"]
    end

    subgraph AlignmentBase["Layer 1: Auto-Alignment Base (The 'Legs')"]
        direction BT
        AzUnit["Azimuth Axis (Horizontal)"]
        AltUnit["Altitude Axis (Vertical)"]
        
        noteBase["> Structure: Worm Gear / Lead Screw\n> Feature: Self-locking, High Rigidity\n> Motors: NEMA 17/23 High Torque"]
        
        AzUnit --"Motorized Rotation"--> AltUnit
        AltUnit -.- noteBase
    end

    subgraph MainBody["Layer 2: Integrated Chassis (The 'Brain')"]
        Housing["Main Housing / Shell"]
        Electronics["Internal Electronics Bay"]
        
        noteBrain["> Contains: RPi 4/5, ESP32, USB Mux\n> Ports: USB, Power, ST4"]
        
        Housing -.-> Electronics
        Electronics -.- noteBrain
    end

    subgraph TrackingHead["Layer 3: Tracking Head (The 'Muscle')"]
        direction BT
        RAUnit["Right Ascension (RA) Axis"]
        DecUnit["Declination (Dec) Axis"]
        
        noteHead["> Structure: Harmonic Drive (17-100)\n> Feature: Zero Backlash, Direct Drive\n> Motors: NEMA 17 (0.9°)"]
        
        RAUnit --"Harmonic Drive"--> DecUnit
        DecUnit -.- noteHead
    end

    subgraph PayloadInterface["Layer 4: Payload & Guiding"]
        Clamp["Dovetail Clamp (Vixen/Losmandy)"]
        Payload["Telescope / Main Camera"]
        GuideScope["Guide Scope (Integrated Handle)"]
        
        noteGuide["> Rigid Connection\n> No 3-Point Rings\n> See guide_scope_design.md"]

        Clamp == "Clamping" ==> Payload
        DecUnit == "Integrated Mount" ==> GuideScope
        GuideScope -.- noteGuide
    end

    %% Physical Connections (Bottom to Top)
    Tripod == "3/8-16 Screw" ==> AzUnit
    AltUnit == "Rigid Connection" ==> Housing
    Housing == "Internal Flange" ==> RAUnit
    DecUnit == "Direct Mount" ==> Clamp

    %% Style
    classDef structural fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef motor fill:#fff9c4,stroke:#fbc02d,stroke-width:1px;
    classDef note fill:#f5f5f5,stroke:#9e9e9e,stroke-width:1px,stroke-dasharray: 5 5;

    class Tripod,Housing,Clamp,Payload structural;
    class AzUnit,AltUnit,RAUnit,DecUnit motor;
    class noteBase,noteBrain,noteHead,noteGuide note;
```

## Mechanical Modules Detail

### 1. Payload Layer
*   **Interface**: Standard Vixen or Losmandy dovetail clamp.
*   **Role**: Securely holds the imaging train (OTA, Camera, Filter Wheel).

### 2. Tracking Head (Upper Layer)
*   **Core Component**: Harmonic Drives (Strain Wave Gears). Recommended model 17-100 or 14-100 depending on payload target.
*   **Advantage**: High torque-to-weight ratio, no counterweight needed for small/medium payloads, zero backlash.
*   **Motors**: NEMA 17 Stepper Motors (0.9° step angle for finer resolution).

### 3. Integrated Chassis (Middle Layer)
*   **Role**: Structural backbone connecting the tracking head to the alignment base.
*   **Internal**: Houses the PCB stack (Motion MCU + SBC + Power + USB Mux).
*   **Cable Management**: Internal routing to minimize cable snagging.

### 4. Alignment Base (Lower Layer)
*   **Role**: Performs the physical Polar Alignment.
*   **Mechanism**:
    *   **Azimuth**: Motorized turntable or push-pull screw driven by stepper.
    *   **Altitude**: Motorized lead screw or worm gear wedge.
*   **Requirement**: Must be self-locking (cannot slip when power is off) and rigid.
*   **Motors**: NEMA 23 or high-torque NEMA 17 to lift the entire assembly weight.
