# CopperPilot Retro Handheld: Parametric 3D Snap-Fit Enclosure

[![CAD Status](https://img.shields.io/badge/CAD-Trimesh%20Parametric%20CSG-brightgreen.svg)](generate_case.py)
[![Test Suite](https://img.shields.io/badge/Tests-15%2F15%20Passed-success.svg)](../tests/test_case.py)
[![3D Print Ready](https://img.shields.io/badge/Print-FDM%20PETG%20%2F%20SLA%20Resin-blue.svg)](#3d-printing--fabrication-guidelines)

A custom, snap-fit handheld console enclosure engineered specifically for the 63.00 mm x 80.00 mm ESP32-S3 retro gaming PCB. The enclosure features a precision front bezel with recessed display viewport, 14 rear vertical heat-dissipation and ergonomics grip grooves, dual bottom wrist lanyard attachment bars, a snap-locking removable Li-Po battery compartment hatch, and floating button keycaps.

---

## 1. Enclosure Geometry & Component Architecture

```
                                [Front Bezel Shell]
                                - 63.0 x 80.0 x 5.2 mm (R=2.5 mm corners)
                                - Recessed 54.57 x 43.22 mm LCD Viewport
                                - D-Pad Cross & ABXY Diamond Keyway Bores
                                - 4x Stepped Alignment Stanchions (H1-H4)
                                - 4x Cantilever Snap Hooks (SL1-SR2)
                                         │
                                         ▼
                                [4-Layer PCBA Assembly]
                                - 63.0 x 80.0 x 1.6 mm FR-4 Board
                                - 4x Through-PCB Cantilever Snap Notches
                                - Front: 14 Tactile Buttons & 2.4" Display
                                - Rear: ESP32-S3, USB-C, Charger, LDO
                                         │
                                         ▼
                                [Rear Grooved Shell]
                                - 63.0 x 80.0 x 11.2 mm (1.8 mm nominal wall)
                                - 14 Precision Vertical Ergonomic Grip Channels
                                - Dual Integrated Wrist Lanyard Anchor Slots
                                - Bottom USB-C Port & Right Side Power Cutouts
                                         │
                                         ▼
                                [Removable Battery Hatch]
                                - 47.8 x 36.8 mm Flush-Fit Li-Po Access Door
                                - Bottom Retention Lip + Top Flexible Snap Tongue
                                - 5x Anti-Slip Thumb Ridges for Toolless Swaps
```

---

## 2. Mechanical Envelope & Mass Budget

| Subassembly / Part | Dimensions (X x Y x Z) | Wall Thickness | Material & Fabrication | Displaced Vol / Mass |
|---|---|---|---|---|
| **Front Bezel** (`case_front_bezel.stl`) | 63.00 x 80.00 x 5.20 mm | 1.80 mm (nominal) | PETG / SLA Tough Resin | ~6.8 cm³ / ~8.6 g |
| **Rear Grooved Shell** (`case_rear_grooved.stl`) | 63.00 x 80.00 x 11.20 mm | 1.80 mm (nominal) | PETG / CNC Aluminum 6061 | ~14.2 cm³ / ~18.0 g |
| **Battery Door** (`case_battery_door.stl`) | 47.80 x 36.80 x 2.20 mm | 1.40 mm | PETG / SLA Resin | ~1.6 cm³ / ~2.0 g |
| **Buttons & Triggers** (`buttons_*.stl`) | D-Pad, ABXY, SE/ST, L1/L2/R1/R2 | Solid | SLA Resin / Silicone | ~2.5 cm³ / ~3.1 g |
| **Mated Console Assembly** | **63.00 x 80.00 x 16.40 mm** | **1.80 mm** | **Complete System** | **~31.7 g (Plastic Shells)** |

---

## 3. Post-Fabrication Snap-Fit Assembly Mechanics

1. **Alignment Pins**: Four stepped cylindrical stanchions on the inside of the front bezel mate with four precision 2.20 mm non-plated through-holes (`H1`, `H2`, `H3`, `H4`) in the PCB corners.
2. **Through-PCB Snap Hooks**: Four cantilever latch beams (`SL1`, `SL2`, `SR1`, `SR2`) pass directly through dedicated 1.20 x 4.40 mm edge notches routed into the PCB perimeter.
3. **90-Degree Retention Undercut**: Once the PCB is pressed home, the 0.50 mm chamfered barb snaps out under the rear PCB ground clearance margin with an insertion force of ~12 N, retaining the PCB securely without screws.
4. **Toolless Battery Door**: The battery hatch slides into a bottom capture channel and clicks into a top spring detent, allowing quick battery replacement without disassembly.

---

## 4. 3D Printing & Fabrication Guidelines

- **Recommended Material**: **PETG** (for snap hook elasticity and thermal resistance up to 75°C) or **SLA Tough / ABS-Like Resin** (for injection-mold grade surface finish).
- **Nozzle / Layer Height**: 0.40 mm nozzle, 0.16 mm or 0.12 mm layer height.
- **Infill**: 100% solid infill on buttons and snap hooks; 25% gyroid infill on outer shells.
- **Print Orientation**:
  - `case_front_bezel.stl`: Place outer front face flat on textured PEI build plate.
  - `case_rear_grooved.stl`: Place back face down (supports required only inside component cavity).
  - `buttons_*.stl`: Print upright on SLA build plate or with fine layer FDM.
