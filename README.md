# CopperPilot Retro Handheld: 4-Layer ESP32-S3 Handheld Console Hardware

[![KiCad EDA](https://img.shields.io/badge/KiCad-v10.0.4-brightgreen.svg)](copperpilot-retro-handheld.kicad_pro)
[![DRC Status](https://img.shields.io/badge/DRC-Zero%20Errors%20%7C%20100%25%20Routed-brightgreen.svg)](copperpilot-retro-handheld.kicad_pcb)
[![ERC Status](https://img.shields.io/badge/ERC-Zero%20Errors-brightgreen.svg)](copperpilot-retro-handheld.kicad_sch)
[![Lion Circuits Turnkey](https://img.shields.io/badge/Fab-Lion%20Circuits%204--Layer-orange.svg)](#lion-circuits-4-layer-manufacturing--pcba-specifications)
[![3D Enclosure](https://img.shields.io/badge/Case-Watertight%20Snap--Fit%20STLs-blue.svg)](case/)
[![Automated Tests](https://img.shields.io/badge/Tests-51%2F51%20Passed-success.svg)](tests/)

The CopperPilot Retro Handheld is an ultra-compact, single-board retro handheld console design built on a 4-layer FR-4 PCB (**63.00 mm x 80.00 mm**) with a parametric snap-fit enclosure. Built around an Espressif ESP32-S3 dual-core microcontroller, the hardware features a 2.4-inch 320x240 ILI9341 SPI color TFT display, 14 responsive gameplay and shoulder pushbuttons, integrated USB-C charging and native USB-OTG/JTAG programming, automatic load-sharing battery power management for uninterrupted gameplay while charging, and a removable 1000 mAh Li-Po cell.

> **Project status:** this repository contains the hardware (schematic, PCB, enclosure CAD, and manufacturing outputs) only. There is **no firmware yet**, so no frame rates, emulator compatibility, or battery runtime have been measured on this board.

---

## 3D Enclosure & Industrial Design Showcase

### 3D CAD Enclosure Renders

| Front Face & Controls | Rear Shell & Grip Channels |
| :---: | :---: |
| ![Front Render](docs/images/case_render_front.png) | ![Rear Render](docs/images/case_render_rear.png) |
| **Front bezel, display window & keycaps** | **Rear grooved shell & battery hatch** |

| 3/4 Isometric View | Exploded Subsystem Assembly |
| :---: | :---: |
| ![Isometric Render](docs/images/case_render_isometric.png) | ![Exploded View](docs/images/case_render_exploded.png) |
| **Assembled enclosure** | **Front Bezel, PCBA, Floating Keycaps, Rear Shell & Door** |

### Complete 3D Assembly Motion Animation (GIF & MP4)

<p align="center">
  <img src="docs/images/case_explosion_animation.gif" alt="3D Assembly Sequence Animation" width="560">
  <br>
  <em>Sequential 3D Assembly Animation: PCBA SMT/TH Component Populating &rarr; Gamepad Keycaps Seating over Tactile Switches &rarr; 2.4" Display Panel Seating &amp; FPC Interconnect into J3 &rarr; Front Bezel Lowering over Controls &amp; Alignment Pins &rarr; Li-Po Battery Seating into Rear Cavity &rarr; Rear Grooved Shell Closing &amp; Flush Snap Mating &rarr; 360&deg; Watertight Turntable Inspection</em>
  <br>
  <strong>High-definition MP4 video asset:</strong> <code>docs/images/case_assembly_video.mp4</code>
</p>

---

## 4-Layer Routed PCB Layout & Schematic Capture

| Front Layer (`F.Cu` — Tactile Controls & Display) | Back Layer (`B.Cu` — ESP32-S3, USB-C & Power ICs) |
| :---: | :---: |
| ![PCB Front Layout](docs/images/pcb_routed_top.png) | ![PCB Back Layout](docs/images/pcb_routed_bottom.png) |

### Photorealistic 3D KiCad PCB Renders (`kicad-cli pcb render`)

| KiCad 3D Top View (Tactile Controls, JST-GH J3 & Top Shoulder Switches) | KiCad 3D Bottom View (ESP32-S3 Module, USB-C, JST-PH & Power Management) |
| :---: | :---: |
| ![KiCad 3D Top](docs/images/pcb_kicad_3d_top.png) | ![KiCad 3D Bottom](docs/images/pcb_kicad_3d_bottom.png) |
| *Populated Front: 14x Tactile Switches, J3 Display Receptacle, D1/D3 LEDs* | *Populated Back: ESP32-S3-WROOM-1, USB-C, JST-PH Battery Header, LDO & Charger* |

<p align="center">
  <img src="docs/images/schematic_render.png" alt="Complete KiCad Schematic Capture" width="900">
  <br>
  <em>Complete 6-Block Schematic Capture (USB-C Power, Li-Po Charger, Load Sharing, ESP32-S3 Core, ILI9341 TFT & 14 Pushbuttons)</em>
</p>

---

## System Architecture

```
                    +-------------------------------------------------------+
                    |                   Power Subsystem                     |
                    | USB-C (J1) ---> USBLC6-2SC6 (U1) ESD Protection       |
                    |                 |                                     |
                    |                 +---> MCP73831 (U2) Charger (500mA)   |
                    |                 |     |                               |
                    |                 |     v                               |
                    |                 |    JST-PH 1S LiPo (J2)              |
                    |                 |     |                               |
                    |                 v     v                               |
                    |           AO3401A (Q1) + MBR0520 (D2) Power Path      |
                    |                       | (Auto Load-Sharing)           |
                    |                       v                               |
                    |              Main Power Switch (SW1)                  |
                    |                       |                               |
                    |                       +---> 100k/100k Divider (IO1)   |
                    |                       v                               |
                    |              AP2112K-3.3 (U3) 600mA LDO               |
                    +-----------------------|-------------------------------+
                                            | +3.3V System Rail
+--------------------------+  Hardware FSPI +-------------------------------+
|  2.4" 320x240 ILI9341    |<---------------|       ESP32-S3-WROOM-1        |
|  SPI Color TFT (J3)      |  SCK, MOSI,    |  Dual-Core Xtensa LX7 240MHz  |
|  2N7002 Backlight Driver |<---------------|  512KB SRAM, 8MB Flash        |
+--------------------------+  CS, DC, RST,  |  2MB PSRAM, Wi-Fi 4 / BLE 5.0 |
                              PWM Backlight +---+---+---+---+---+---+---+---+
                                                |   |   |   |   |   |   |
     14x Active-Low Tactile Pushbuttons:        |   |   |   |   |   |   |
     D-Pad (Up, Down, Left, Right) <------------+   |   |   |   |   |   |
     Action Diamond (A, B, X, Y) <------------------+   |   |   |   |   |
     Utility Controls (Select, Start) <-----------------+   |   |   |   |
     Shoulder Triggers (L1, L2, R1, R2) <-------------------+   |   |   |
     Boot & Reset Service Switches (SW2, SW3) <-----------------+---+---+
```

---

## Hardware Specifications & Computational Capability

- **Chassis & Form Factor**: 63.00 mm x 80.00 mm ultra-compact 4-layer FR-4 PCB with R=2.50 mm corner radii, 4 precision 2.20 mm alignment holes (`H1`–`H4`), and 4 through-PCB snap-hook retention notches (`SL1`, `SL2`, `SR1`, `SR2`).
- **Core Processing Unit**: Espressif ESP32-S3-WROOM-1-N8R2 (dual-core 32-bit Xtensa LX7 @ 240 MHz, 512 KB internal SRAM, 8 MB Quad-SPI Flash, 2 MB Quad-SPI PSRAM, 2.4 GHz 802.11 b/g/n Wi-Fi + Bluetooth 5.0 LE).
  - **Game & Emulator Capability (not yet verified on this board)**: There is no firmware for this board yet, so no frame rates or emulator results are claimed here. The figures below are design-level estimates and third-party reports from other ESP32-S3 hardware, cited for reference only:
    - Display link: the ESP32-S3 SPI2 (FSPI) peripheral supports DMA transfers. A full 320x240 RGB565 frame is 150 KB (300 KB double-buffered, well within the 2 MB PSRAM). Achievable frame rate depends on the SPI clock the ILI9341 panel and cabling sustain in practice (commonly 40 MHz). The [esp-box-emu](https://github.com/esp-cpp/esp-box-emu) project reports a "~31 fps ceiling" for 320x240x16bpp output on its ESP32-S3 panel.
    - Emulators on other ESP32-S3 devices: [esp-box-emu](https://github.com/esp-cpp/esp-box-emu) runs NES (nofrendo), Game Boy / Game Boy Color (gnuboy), Sega Master System / Game Gear, Genesis and Doom on the ESP32-S3-BOX. [Retro-Go](https://github.com/ducalex/retro-go) supports NES, Game Boy / Color, Master System, Game Gear, PC Engine and more on ESP32 handhelds, with ESP32-S3 community ports. [PaperBoy S3](https://www.tomshardware.com/video-games/retro-gaming/designer-turns-niche-e-ink-dev-board-into-a-60hz-game-boy-handheld-960x540-display-powered-by-ultra-low-cost-esp32-s3-microcontroller) (Tom's Hardware) runs a Game Boy emulator on an ESP32-S3, with the chip fully loaded.
    - These results come from different hardware and firmware. Performance on this board has to be measured once firmware exists.
    - *Audio note*: The board does not integrate an analog audio amplifier or speaker. Audio is supported wirelessly via Bluetooth 5.0 LE / A2DP or via external PWM buzzer on spare GPIO.
- **Display Subsystem & Connector `J3`**:
  - **Board-Mounted SMT Socket (`J3`)**: JST Sales America `SM10B-GHS-TB(LF)(SN)` (10-position 1.25 mm pitch horizontal SMD header with solder retention tabs).
  - **Turnkey Sourced Display Module (`DISP1`)**: **Waveshare 15933** (MPN: `15933` / DigiKey: `2649-15933-ND` / LCSC: `C2913222`) or EastRising `ER-TFT024-3`.
    - 2.4-inch 320x240 RGB TFT LCD, Sitronix/Ilitek ILI9341 4-wire SPI controller, 3.3V DC logic, active area 48.96 x 36.72 mm, 10-conductor cable harness with mating plug JST `GHR-10V-S`.
  - Onboard 2N7002 N-channel MOSFET backlight switch (`Q2`) with 10 Ω ballast resistor (`R14`) and 100 kHz PWM brightness dimming on GPIO21.
- **Power Management & Dynamic Load-Sharing**:
  - Microchip MCP73831T-2ACI/OT linear Li-Po/Li-Ion charge management controller configured for 500 mA fast charge (`R_PROG` = 2.0 kΩ 1%).
  - Automatic dynamic load sharing via AO3401A P-channel MOSFET (`Q1`, $R_{DS(on)} < 50\text{ m}\Omega$) and MBR0520 Schottky barrier diode (`D2`, $V_F = 0.38\text{ V}$). When 5V USB-C is plugged in, the system runs directly off USB power while the battery charges undisturbed at its full C-rate; upon disconnect, the MOSFET transparently switches system load back to battery without voltage droop.
  - Diodes Inc. AP2112K-3.3 ultra-low-dropout 600 mA CMOS regulator with 250 mV dropout voltage, powering the console reliably down to 3.55 V battery cutoff.
  - Precision 100 kΩ / 100 kΩ 1% resistor divider (`R8`, `R9`) with 100 nF smoothing capacitor (`C6`) on ESP32-S3 `ADC1_CH0` (GPIO1) for fuel gauge battery telemetry.
  - Estimated system consumption (design estimate, not measured): ~220 mA @ 3.3V (~0.73W) with display backlight at 100% and CPU at 240 MHz, which would give roughly 4.5 hours from a 1000 mAh Li-Po cell.
- **Controls & Non-Colliding 3D Keycaps**:
  - 14 front-mounted tactile switches with 10 kΩ pull-up networks:
    - 4-way D-Pad (`UP`, `DOWN`, `LEFT`, `RIGHT`) centered at (14.65, 60.96 mm).
    - 4-button action diamond (`A`, `B`, `X`, `Y`) centered at (47.97, 61.75 mm).
    - 2 utility buttons (`SELECT`, `START`) centered at (31.24, 69.70 mm).
    - 4 shoulder triggers (`L1`, `L2`, `R1`, `R2`) centered at (9.50, 18.33, 53.50, 44.67 mm).
  - **Guaranteed Physical Clearances**:
    - D-Pad to Select button flange clearance: **1.49 mm** (zero collision).
    - ABXY adjacent button flange clearance: **>1.22 mm** between all neighboring pairs.
    - L1/L2 and R2/R1 shoulder trigger gap: **0.93 mm** inter-button clearance.
    - Keycap-to-bezel sliding clearance: **0.30 mm** radial clearance for friction-free actuation.

---

## Lion Circuits 4-Layer Manufacturing & PCBA Specifications

The hardware has been validated against Lion Circuits India turnkey PCBA design and procurement standards:

| Fabrication Parameter | Lion Circuits Standard Capability | Handheld Console Implementation | Design Margin |
| :--- | :--- | :--- | :--- |
| **Layer Count** | 4-Layer Multi-Layer FR-4 | **4 Layers** (`F.Cu`, `In1.Cu`, `In2.Cu`, `B.Cu`) | Standard |
| **Finished Thickness** | 1.6 mm nominal (+/- 10%) | **1.60 mm** | Exact Nominal |
| **Copper Weight** | 1.0 oz outer / 0.5 oz inner | **1.0 oz (35 µm) outer / 0.5 oz (17.5 µm) inner** | Standard |
| **Minimum Trace Width** | 6 mil (0.1524 mm) | **6 mil (0.1524 mm) min / 8 mil (0.20 mm) typ** | 100% Fab Compliant |
| **Minimum Trace Spacing** | 6 mil (0.1524 mm) | **6 mil (0.1524 mm) min / 8 mil (0.20 mm) typ** | 100% Fab Compliant |
| **Via Drill & Diameter** | 0.30 mm drill / 0.60 mm pad | **0.30 mm drill / 0.60 mm diameter** | Exact Standard Spec |
| **Annular Ring** | 6 mil (0.152 mm) minimum | **0.150 mm (6 mil)** | 100% Fab Compliant |
| **Copper to Board Edge** | 12 mil (0.30 mm) minimum | **0.40 mm (16 mil)** | +33% Safety Margin |
| **Surface Finish** | Lead-Free HASL or ENIG | **Electroless Nickel Immersion Gold (ENIG)** | Superior SMT Coplanarity |
| **Solder Mask & Silk** | Matte Black Mask / White Silk | **Matte Black / High-Contrast White** | Premium Aesthetic |

### Turnkey PCBA Bill of Materials (45 Verified Line Items)

| Item | Designators | Qty | Part / Value | Manufacturer | MPN | Package | Sourcing Channel |
| :---: | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| 1 | `U4` | 1 | Dual-Core MCU + PSRAM | Espressif Systems | `ESP32-S3-WROOM-1-N8R2` | SMD-41 (18x25.5mm) | DigiKey / Mouser / LCSC |
| 2 | `J1` | 1 | USB-C 2.0 16-Pin Receptacle | GCT / Hroparts | `USB4105-GF-A` / `TYPE-C-31-M-12` | USB-C-16P-TopMount | DigiKey / LCSC |
| 3 | `U1` | 1 | Rail-to-Rail ESD Diode Array | STMicroelectronics | `USBLC6-2SC6` | SOT-23-6 | DigiKey / Mouser |
| 4 | `U2` | 1 | 500mA Li-Po Charger | Microchip Technology | `MCP73831T-2ACI/OT` | SOT-23-5 | DigiKey / Mouser |
| 5 | `Q1` | 1 | P-MOSFET Load Sharing | Alpha & Omega Semi | `AO3401A` | SOT-23 | DigiKey / LCSC |
| 6 | `D2` | 1 | 20V 0.5A Schottky Diode | ON Semiconductor | `MBR0520LT1G` | SOD-123 | DigiKey / Mouser |
| 7 | `U3` | 1 | 600mA Ultra-Low-Dropout LDO | Diodes Incorporated | `AP2112K-3.3TRG1` | SOT-23-5 | DigiKey / Mouser |
| 8 | `Q2` | 1 | 60V 300mA N-MOSFET Backlight | Nexperia | `2N7002,215` | SOT-23 | DigiKey / Mouser |
| 9 | `D1` | 1 | Red LED (Charge Indicator) | Lite-On Inc. | `LTST-C190KRKT` | 0603 SMD | DigiKey / Mouser |
| 10 | `D3` | 1 | Green LED (Power Good) | Lite-On Inc. | `LTST-C190KGKT` | 0603 SMD | DigiKey / Mouser |
| 11 | `J2` | 1 | JST-PH 2-Pin Battery Header | JST Sales America | `S2B-PH-K-S(LF)(SN)` | JST_PH_1x02_P2.00mm | DigiKey / Mouser |
| 12 | `J3` | 1 | JST-GH 10-Pin Display Socket | JST Sales America | `SM10B-GHS-TB(LF)(SN)` | 10-Pin 1.25mm SMT | DigiKey / Mouser |
| 13 | `SW1` | 1 | SPDT Power Slide Switch | C&K / Hroparts | `PCM12SMTR` / `MSK-12C02` | SMT Slide Switch | DigiKey / LCSC |
| 14 | `SW4`-`SW11` | 8 | 6x6mm Tactile Switches | C&K Components | `PTS645SM43SMTR92 LFS` | 6.0x6.0mm SMD | DigiKey / Mouser |
| 15 | `SW12`,`SW13`,`SW2`,`SW3` | 4 | 6x3.5mm Tactile Switches | C&K Components | `PTS636 SM25 LFS` | 6.0x3.5mm SMD | DigiKey / Mouser |
| 16 | `SW14`-`SW17` | 4 | Ultra-Small Tactile Switches | Omron Electronics | `B3U-3000P` | 3.0x2.5mm SMD | DigiKey / Mouser |
| 17 | `DISP1` | 1 | 2.4" 320x240 ILI9341 SPI TFT | Waveshare / EastRising | `15933` / `ER-TFT024-3` | 2.4" Module + Cable | DigiKey / LCSC / Waveshare |
| 18 | `BT1` | 1 | 3.7V 1000mAh 1S Li-Po Cell | PKCELL / Adafruit | `LP803040` / `ID 258` | 40x30x8.0mm JST-PH | DigiKey / Adafruit |
| 19 | `CASE1` | 1 | CopperPilot Retro Handheld 3D Snap-Fit Case Kit | CopperPilot (in-house design) | `CP-RETRO-HANDHELD-CASE-V1` | 3D Watertight Enclosure | 3D Printed / Molded |
| 20-34 | `C1`-`C15` | 15 | Ceramic MLCC Decoupling | Yageo / Murata | 100nF, 1uF, 4.7uF, 10uF, 22uF | 0603 & 0805 | DigiKey / LCSC |
| 35-45 | `R1`-`R30` | 30 | Precision Chip Resistors | Yageo / Vishay | 10, 22, 1k, 2k 1%, 5.1k, 10k, 100k 1% | 0603 & 0805 | DigiKey / LCSC |

---

## Automated Verification Suite

The repository includes a **51-point automated PyTest hardware, assembly, and enclosure verification suite**:

```bash
$ make test
============================= test session starts ==============================
platform linux -- Python 3.13.9, pytest-9.1.1
collected 51 items

tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage1_pcba_component_loading PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage2_kicad_3d_pcba_mesh_validation PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage3_buttons_clearance_and_zero_collision PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage4_buttons_seat_onto_pcba_zero_collision PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage5_buttons_seat_in_front_bezel_zero_collision PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage6_display_shelf_mating_and_j3_interconnect PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage7_pcba_mating_to_front_bezel_zero_collision PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage8_rear_shell_mating_over_pcb_zero_collision PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage9_battery_seating_and_rear_cavity_fit PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage10_continuous_kinematic_assembly_trajectories PASSED
tests/test_assembly_e2e.py::TestEndToEndAssemblySequence::test_stage11_full_console_assembly_envelope PASSED
tests/test_case.py::TestCaseFiles::test_stl_file_exists[case_front_bezel.stl] PASSED
tests/test_case.py::TestCaseFiles::test_stl_file_exists[case_rear_grooved.stl] PASSED
tests/test_case.py::TestCaseFiles::test_stl_file_exists[case_battery_door.stl] PASSED
tests/test_case.py::TestCaseFiles::test_stl_file_exists[buttons_dpad_abxy_sest_shoulders.stl] PASSED
tests/test_case.py::TestCaseFiles::test_stl_file_exists[copperpilot_retro_handheld_assembly.stl] PASSED
tests/test_case.py::TestCaseGeometry::test_front_bezel_envelope PASSED
tests/test_case.py::TestCaseGeometry::test_rear_shell_envelope PASSED
tests/test_case.py::TestCaseGeometry::test_battery_door_envelope PASSED
tests/test_case.py::TestCaseGeometry::test_mesh_manifolds_and_faces PASSED
tests/test_case.py::TestCaseGeometry::test_full_assembly_mesh PASSED
tests/test_case.py::TestCaseClearancesAndCollisions::test_all_buttons_zero_collision PASSED
tests/test_case.py::TestCaseClearancesAndCollisions::test_abxy_adjacent_flange_clearances PASSED
tests/test_case.py::TestCaseClearancesAndCollisions::test_dpad_to_select_clearance PASSED
tests/test_case.py::TestCaseClearancesAndCollisions::test_shoulder_buttons_clearance PASSED
tests/test_case.py::TestCaseClearancesAndCollisions::test_snap_fit_engagement_and_boss_alignment PASSED
tests/test_pcb.py::TestBoardPhysical::test_board_dimensions PASSED
tests/test_pcb.py::TestBoardPhysical::test_four_layer_stackup PASSED
tests/test_pcb.py::TestBoardPhysical::test_edge_cuts_closed_contour PASSED
tests/test_pcb.py::TestConnectivityAndNetlist::test_drc_zero_unconnected_items PASSED
tests/test_pcb.py::TestConnectivityAndNetlist::test_drc_zero_errors PASSED
tests/test_pcb.py::TestConnectivityAndNetlist::test_erc_zero_errors PASSED
tests/test_pcb.py::TestConnectivityAndNetlist::test_all_critical_nets_present PASSED
tests/test_pcb.py::TestConnectivityAndNetlist::test_no_dangling_track_stubs PASSED
tests/test_pcb.py::TestConnectivityAndNetlist::test_no_unassigned_vias PASSED
tests/test_pcb.py::TestTraceGeometryAndDFM::test_signal_trace_min_width PASSED
tests/test_pcb.py::TestTraceGeometryAndDFM::test_power_rail_trace_widths PASSED
tests/test_pcb.py::TestTraceGeometryAndDFM::test_via_drill_and_annular_ring PASSED
tests/test_pcb.py::TestTraceGeometryAndDFM::test_zero_clearance_errors PASSED
tests/test_pcb.py::TestSubsystemsAndComponents::test_mcu_esp32s3_placement PASSED
tests/test_pcb.py::TestSubsystemsAndComponents::test_usb_c_and_esd_protection PASSED
tests/test_pcb.py::TestSubsystemsAndComponents::test_power_management_and_charger PASSED
tests/test_pcb.py::TestSubsystemsAndComponents::test_power_path_and_regulator PASSED
tests/test_pcb.py::TestSubsystemsAndComponents::test_display_connector_on_front PASSED
tests/test_pcb.py::TestSubsystemsAndComponents::test_all_14_front_tactile_switches PASSED
tests/test_pcb.py::TestSubsystemsAndComponents::test_boot_and_reset_tactile_switches PASSED
tests/test_pcb.py::TestGroundPlanesAndZoning::test_ground_planes_exist PASSED
tests/test_pcb.py::TestGroundPlanesAndZoning::test_ground_via_density PASSED
tests/test_pcb.py::Test3DModelsAndSilkscreen::test_all_footprints_have_3d_models PASSED
tests/test_pcb.py::Test3DModelsAndSilkscreen::test_no_legacy_kicad_env_vars PASSED
tests/test_pcb.py::Test3DModelsAndSilkscreen::test_pin1_polarity_indicators PASSED

============================== 51 passed ==============================
```

---

## Repository Structure

```
.
├── Makefile                            # Top-level orchestrator (test, drc, erc, fab, gerbers)
├── .gitignore                          # Comprehensive Git exclusion rules
├── LICENSE                             # CERN Open Hardware Licence v2 - Permissive
├── README.md                           # Master hardware, pinout, and manufacturing documentation
├── export_manufacturing.py             # Lion Circuits release generator (Gerbers, CPL, BOM, D356)
├── copperpilot-retro-handheld.kicad_pro       # KiCad 10 project definition & netclass rules
├── copperpilot-retro-handheld.kicad_sch       # Hierarchical schematic capture (0 ERC errors)
├── copperpilot-retro-handheld.kicad_pcb       # 4-layer PCB layout (100% routed, 0 DRC violations)
├── sym-lib-table                       # Symbol library mapping
├── fp-lib-table                        # Footprint library mapping
├── libs/                               # Custom symbols and footprints
│   ├── copperpilot_retro_handheld.kicad_sym      # Custom ILI9341 2.4" TFT display symbol
│   └── copperpilot_retro_handheld.pretty/        # Custom 10-pin display footprint & 3D model
├── tests/                              # Automated 51-point hardware & assembly verification suite
│   ├── conftest.py                     # S-expression AST parsers & KiCad CLI fixtures
│   ├── test_assembly_e2e.py            # 11-stage end-to-end mechanical assembly verification
│   ├── test_pcb.py                     # 25-point PCB geometry, connectivity, DFM & circuit tests
│   └── test_case.py                    # 15-point 3D mechanical enclosure & clearance tests
├── case/                               # Parametric 3D snap-fit enclosure CAD subsystem
│   ├── Makefile                        # Targets: generate, render, test, clean
│   ├── README.md                       # Enclosure mechanics, snap-fit physics & 3D print specs
│   ├── generate_case.py                # Parametric CSG mesh synthesis in Trimesh & Manifold3D
│   ├── render_case.py                  # High-resolution PyVista rendering & animation engine
│   ├── models/                         # Watertight production-ready STL models
│   │   ├── case_front_bezel.stl        # Front bezel with screen window & non-colliding bores
│   │   ├── case_rear_grooved.stl       # Rear shell with 14 grip channels & snap catch pockets
│   │   ├── case_battery_door.stl       # Removable battery bay hatch with retention lip
│   │   ├── buttons_dpad_abxy_*.stl     # Complete set of floating button keycaps (>1.2mm gap)
│   │   └── copperpilot_retro_handheld_assembly.stl # Full mated console assembly
│   └── renders/                        # Multi-view isometric, front, rear, and exploded renders
└── docs/
    └── images/                         # Documentation renders and animations
        ├── case_render_*.png           # Front, rear, isometric & exploded CAD renders
        ├── case_explosion_animation.gif# 64-frame 3D sequential assembly motion animation
        └── case_assembly_video.mp4     # High-definition MP4 assembly video asset
```

---

## Quickstart & Manufacturing Commands

Ensure `kicad-cli` (v10.0+) and Python 3.10+ (with `uv`) are available in your path:

### 1. Run Automated Verification & Rule Checks
```bash
# Run full 51-point PyTest verification suite (installs test deps via uv)
make test

# Run electrical rule check (ERC) via KiCad CLI
kicad-cli sch erc copperpilot-retro-handheld.kicad_sch

# Run design rule check (DRC) via KiCad CLI
kicad-cli pcb drc copperpilot-retro-handheld.kicad_pcb
```

### 2. Generate 3D CAD Enclosure STLs and Visuals
```bash
# Generate watertight STL models
make build-case

# Render smooth anti-aliased images and assembly animation
make render-case
```

### 3. Generate Turnkey Manufacturing Release Bundle
```bash
# Generate gerbers, drill, CPL, structured BOM, and release zip
make fab
```
