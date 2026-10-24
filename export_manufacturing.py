#!/usr/bin/env python3
"""
GKD Pixel ESP32-S3 Handheld Console - Turnkey Manufacturing Release Generator
Targets Lion Circuits 4-Layer FR-4 Manufacturing and SMT Turnkey PCBA.
"""

import argparse
import csv
import os
import re
import subprocess
import zipfile

PROJECT_NAME = "gameboy-copperpilot"
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
PCB_FILE = os.path.join(ROOT_DIR, f"{PROJECT_NAME}.kicad_pcb")
SCH_FILE = os.path.join(ROOT_DIR, f"{PROJECT_NAME}.kicad_sch")
BUILD_DIR = os.path.join(ROOT_DIR, "build")
GERBER_DIR = os.path.join(BUILD_DIR, "gerbers")
RELEASE_ZIP = os.path.join(BUILD_DIR, f"{PROJECT_NAME}_LionCircuits_Release.zip")
GERBERS_ZIP = os.path.join(BUILD_DIR, f"{PROJECT_NAME}_Gerbers.zip")


# Complete verified BOM mapping for Lion Circuits PCBA procurement
BOM_DATABASE = {
    "ESP32-S3-WROOM-1": {
        "mfr": "Espressif Systems",
        "mpn": "ESP32-S3-WROOM-1-N8R2",
        "desc": "Dual-Core Xtensa LX7 @ 240MHz, 8MB Flash, 2MB PSRAM, Wi-Fi 4/BLE 5.0",
        "package": "SMD-41 (18x25.5mm)",
    },
    "USB_C_Receptacle_USB2.0_16P": {
        "mfr": "Korean Hroparts Elec / GCT",
        "mpn": "TYPE-C-31-M-12 / USB4105-GF-A",
        "desc": "USB 2.0 Type-C 16-pin Receptacle Top-Mount SMT + 4 TH Shield Tabs",
        "package": "USB-C-16P-TopMount",
    },
    "USBLC6-2SC6": {
        "mfr": "STMicroelectronics",
        "mpn": "USBLC6-2SC6",
        "desc": "Very Low Capacitance ESD Protection Diode Array, 2-line Rail-to-Rail",
        "package": "SOT-23-6",
    },
    "MCP73831-2-OT": {
        "mfr": "Microchip Technology",
        "mpn": "MCP73831T-2ACI/OT",
        "desc": "Miniature Single-Cell 500mA Li-Po/Li-Ion Charge Management Controller",
        "package": "SOT-23-5",
    },
    "AO3401A": {
        "mfr": "Alpha & Omega Semiconductor",
        "mpn": "AO3401A",
        "desc": "P-Channel MOSFET -30V, -4.0A, RDS(on) < 50mOhm @ -4.5V",
        "package": "SOT-23",
    },
    "MBR0520": {
        "mfr": "ON Semiconductor",
        "mpn": "MBR0520LT1G",
        "desc": "Schottky Barrier Diode 20V 0.5A, Low VF = 0.38V",
        "package": "SOD-123",
    },
    "AP2112K-3.3": {
        "mfr": "Diodes Incorporated",
        "mpn": "AP2112K-3.3TRG1",
        "desc": "Ultra-Low Dropout 600mA CMOS LDO Regulator, 250mV Vdo, 55uA Iq",
        "package": "SOT-23-5",
    },
    "2N7002": {
        "mfr": "Nexperia / ON Semi",
        "mpn": "2N7002,215",
        "desc": "N-Channel TrenchFET 60V 300mA RDS(on) 2.8 Ohm",
        "package": "SOT-23",
    },
    "LED_RED": {
        "mfr": "Lite-On Inc.",
        "mpn": "LTST-C190KRKT",
        "desc": "Red LED 639nm 54mcd 20mA 0603 SMD (Charge Status)",
        "package": "LED_0603_1608Metric",
    },
    "LED_GREEN": {
        "mfr": "Lite-On Inc.",
        "mpn": "LTST-C190KGKT",
        "desc": "Green LED 571nm 35mcd 20mA 0603 SMD (Power Good)",
        "package": "LED_0603_1608Metric",
    },
    "Conn_01x02": {
        "mfr": "JST Sales America",
        "mpn": "S2B-PH-K-S(LF)(SN)",
        "desc": "Connector Header 2.00mm Pitch 2-Position Right Angle Shrouded",
        "package": "JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal",
    },
    "ILI9341_TFT_2.4in": {
        "mfr": "JST Sales America",
        "mpn": "SM10B-GHS-TB(LF)(SN)",
        "desc": "10-Pin 1.25mm Pitch Horizontal SMT Shrouded Header for Waveshare 15933 / ER-TFT024-3 Display",
        "package": "ILI9341_TFT_2.4in_10P",
    },
    "SW_SPDT": {
        "mfr": "C&K / Korean Hroparts",
        "mpn": "SS-12D00G3 / MSK-12C02",
        "desc": "SPDT Slide Switch Right Angle Through-Hole, Power On/Off",
        "package": "SW_SPDT_PCM12",
    },
}


def ensure_dirs():
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(GERBER_DIR, exist_ok=True)


def export_gerbers():
    ensure_dirs()
    print("==> [1/8] Exporting 4-Layer RS-274X Gerbers for Lion Circuits...")
    layers = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,F.Paste,B.Paste,Edge.Cuts"
    cmd = [
        "kicad-cli",
        "pcb",
        "export",
        "gerbers",
        "-l",
        layers,
        "--no-x2",
        "--subtract-soldermask",
        "-o",
        f"{GERBER_DIR}/",
        PCB_FILE,
    ]
    subprocess.run(cmd, check=True)
    print("    Gerber layers exported successfully.")


def export_drill():
    ensure_dirs()
    print("==> [2/8] Exporting NC Excellon Drill Files...")
    cmd = [
        "kicad-cli",
        "pcb",
        "export",
        "drill",
        "--format",
        "excellon",
        "--drill-origin",
        "absolute",
        "--excellon-separate-th",
        "-o",
        f"{GERBER_DIR}/",
        PCB_FILE,
    ]
    subprocess.run(cmd, check=True)
    print("    NC Drill files exported successfully.")


def zip_gerbers():
    ensure_dirs()
    print(f"==> [3/8] Packaging Gerber Release Archive ({GERBERS_ZIP})...")
    with zipfile.ZipFile(GERBERS_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in sorted(os.listdir(GERBER_DIR)):
            fpath = os.path.join(GERBER_DIR, fname)
            if os.path.isfile(fpath):
                zf.write(fpath, arcname=fname)
    print(f"    Saved {GERBERS_ZIP} ({os.path.getsize(GERBERS_ZIP) // 1024} KB).")


def export_cpl():
    ensure_dirs()
    print("==> [4/8] Generating SMT Component Centroid / Pick-and-Place (CPL) File...")
    cpl_path = os.path.join(BUILD_DIR, "cpl.csv")
    cmd = [
        "kicad-cli",
        "pcb",
        "export",
        "pos",
        "--side",
        "both",
        "--format",
        "csv",
        "--units",
        "mm",
        "-o",
        cpl_path,
        PCB_FILE,
    ]
    subprocess.run(cmd, check=True)
    print(f"    Saved centroid pick-and-place data to {cpl_path}.")


def export_bom():
    ensure_dirs()
    print("==> [5/8] Generating Structured Turnkey Bill of Materials (BOM)...")
    bom_path = os.path.join(BUILD_DIR, "bom.csv")

    with open(PCB_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract all footprints
    footprints = []
    fp_pattern = re.finditer(r'\(footprint\s+"([^"]+)"', content)
    fp_matches = list(fp_pattern)
    for i, m in enumerate(fp_matches):
        start = m.start()
        end = fp_matches[i + 1].start() if i + 1 < len(fp_matches) else len(content)
        block = content[start:end]

        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)
        if not ref_m or not val_m:
            continue
        ref = ref_m.group(1)
        val = val_m.group(1)
        fp_id = m.group(1)

        footprints.append({"ref": ref, "val": val, "fp": fp_id})

    # Group by (val, fp)
    groups = {}
    for item in footprints:
        key = (item["val"], item["fp"])
        if key not in groups:
            groups[key] = {"val": item["val"], "fp": item["fp"], "refs": []}
        groups[key]["refs"].append(item["ref"])

    def natural_sort_key(s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

    rows = []
    for (val, fp), data in groups.items():
        refs = sorted(data["refs"], key=natural_sort_key)
        qty = len(refs)
        ref_str = ", ".join(refs)

        # Lookup in BOM database
        entry = BOM_DATABASE.get(val, {})
        if not entry:
            if refs[0].startswith("SW"):
                if "PTS645" in fp:
                    entry = {
                        "mfr": "C&K / Omron",
                        "mpn": "PTS645SM43SMTR92 LFS",
                        "desc": "Tactile Switch SPST 6.0x6.0mm SMD 4.3mm Actuator (D-Pad & Action)",
                        "package": fp.split(":")[-1],
                    }
                elif "PTS636" in fp:
                    entry = {
                        "mfr": "C&K Components",
                        "mpn": "PTS636 SM25 LFS",
                        "desc": "Tactile Switch SPST-NO 6.0x3.5mm SMD 2.5mm Actuator (Select/Start/Boot/Reset)",
                        "package": fp.split(":")[-1],
                    }
                elif "B3U" in fp:
                    entry = {
                        "mfr": "Omron Electronics",
                        "mpn": "B3U-3000P",
                        "desc": "Ultra-Small Tactile Switch SPST-NO SMD 3.0x2.5x1.2mm (Shoulder Triggers)",
                        "package": fp.split(":")[-1],
                    }
                else:
                    entry = {
                        "mfr": "C&K / Korean Hroparts",
                        "mpn": "SS-12D00G3 / MSK-12C02",
                        "desc": "SPDT Slide Switch Right Angle Through-Hole, Power On/Off",
                        "package": fp.split(":")[-1],
                    }
            elif refs[0].startswith("C") or val.endswith(("uF", "nF", "pF")):
                entry = {
                    "mfr": "Yageo / Murata / Samsung",
                    "mpn": f"Generic MLCC {val} 16V-50V X5R/X7R",
                    "desc": f"Capacitor Ceramic SMD {val} +/-10%",
                    "package": fp.split(":")[-1],
                }
            elif refs[0].startswith("R"):
                entry = {
                    "mfr": "Yageo / Vishay / Panasonic",
                    "mpn": f"Generic Resistor {val} 1% 1/10W",
                    "desc": f"Thick Film Chip Resistor {val} 1%",
                    "package": fp.split(":")[-1],
                }
            else:
                entry = {
                    "mfr": "Standard",
                    "mpn": val,
                    "desc": val,
                    "package": fp.split(":")[-1],
                }

        rows.append(
            {
                "Designator": ref_str,
                "Quantity": qty,
                "Value": val,
                "Footprint": fp.split(":")[-1],
                "Manufacturer": entry.get("mfr", "Generic"),
                "MPN": entry.get("mpn", val),
                "Description": entry.get("desc", val),
            }
        )

    # Add turnkey module line items required for full system assembly
    rows.append(
        {
            "Designator": "DISP1",
            "Quantity": 1,
            "Value": "2.4in_ILI9341_SPI_TFT",
            "Footprint": "Module:TFT_2.4in_320x240",
            "Manufacturer": "Waveshare Electronics / EastRising",
            "MPN": "15933 (Waveshare 2.4inch LCD Module) / ER-TFT024-3",
            "Description": "2.4-inch 320x240 RGB Color TFT Display, ILI9341 SPI Controller, 3.3V Logic with 10-pin JST GH Cable",
        }
    )
    rows.append(
        {
            "Designator": "BT1",
            "Quantity": 1,
            "Value": "1000mAh_3.7V_LiPo",
            "Footprint": "Battery:1S_LiPo_40x30x8mm",
            "Manufacturer": "PKCELL / Adafruit",
            "MPN": "LP803040 / ID 258",
            "Description": "3.7V 1000mAh 1S Li-Po Rechargeable Battery with JST-PH 2.00mm 2-Pin Female Connector",
        }
    )
    rows.append(
        {
            "Designator": "CASE1",
            "Quantity": 1,
            "Value": "GKD_Pixel_3D_Case_Kit",
            "Footprint": "Enclosure:GKD_Pixel_63x80mm",
            "Manufacturer": "GKD Pixel Custom",
            "MPN": "GKD-PIXEL-CASE-V1",
            "Description": "Full 3D Snap-Fit Enclosure Kit (Front Bezel, Rear Shell, Battery Hatch, D-Pad, ABXY, SE/ST, Shoulders)",
        }
    )

    rows.sort(key=lambda r: natural_sort_key(r["Designator"].split(", ")[0]))

    fieldnames = [
        "Designator",
        "Quantity",
        "Value",
        "Footprint",
        "Manufacturer",
        "MPN",
        "Description",
    ]
    with open(bom_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"    Saved structured BOM to {bom_path} ({len(rows)} line items).")


def export_d356():
    ensure_dirs()
    print("==> [6/8] Generating IPC-D-356 Electrical Test Netlist...")
    out_path = os.path.join(BUILD_DIR, f"{PROJECT_NAME}.d356")
    cmd = ["kicad-cli", "pcb", "export", "ipcd356", "-o", out_path, PCB_FILE]
    subprocess.run(cmd, check=True)
    print(f"    Saved IPC-D-356 netlist to {out_path}.")


def export_pdf():
    ensure_dirs()
    print("==> [7/8] Generating Schematic & Multi-Layer PCB Assembly PDFs...")
    sch_pdf = os.path.join(BUILD_DIR, f"{PROJECT_NAME}_Schematic.pdf")
    pcb_pdf = os.path.join(BUILD_DIR, f"{PROJECT_NAME}_PCB_Layers.pdf")

    subprocess.run(
        ["kicad-cli", "sch", "export", "pdf", "-o", sch_pdf, SCH_FILE], check=True
    )
    subprocess.run(
        [
            "kicad-cli",
            "pcb",
            "export",
            "pdf",
            "-l",
            "F.Cu,B.Cu,In1.Cu,In2.Cu,F.SilkS,B.SilkS,Edge.Cuts",
            "-o",
            pcb_pdf,
            PCB_FILE,
        ],
        check=True,
    )
    print(f"    Saved {sch_pdf} and {pcb_pdf}.")


def export_spec():
    ensure_dirs()
    spec_path = os.path.join(BUILD_DIR, "ORDER_SPEC.md")
    content = """# Lion Circuits Turnkey PCB Fabrication & PCBA Assembly Specification

## 1. PCB Board Fabrication Parameters
- **Project Name**: GKD Pixel ESP32-S3 Handheld Gaming Console (`gameboy-copperpilot`)
- **Dimensions**: 63.00 mm x 80.00 mm (Finished unit with R=2.5mm corner radii)
- **Panelization Strategy**: 63.00 mm x 105.00 mm Carrier Panel (with 2x 12.5mm breakaway tooling rails on 63mm edges, exceeding Lion Circuits 50x100mm conveyor minimum)
- **Layer Count**: 4-Layer FR-4 (TG140-150)
- **Board Thickness**: 1.60 mm +/- 10%
- **Copper Thickness**:
  - Outer Layers (F.Cu, B.Cu): 1.0 oz (35 um)
  - Inner Layers (In1.Cu GND, In2.Cu Signal): 0.5 oz (17.5 um)
- **Surface Finish**: Electroless Nickel Immersion Gold (ENIG) (Critical for 0.5mm USB-C and FPC pads)
- **Solder Mask**: Matte Black (both sides)
- **Silkscreen**: White (both sides)
- **Min Trace Width / Clearance**: 0.1524 mm / 0.1524 mm (6 mil / 6 mil)
- **Min Hole / Annular Ring**: 0.30 mm drill / 0.60 mm pad (0.15 mm annular ring)
- **Depaneling Method**: Routed 2.0 mm kerf with mouse-bite perforations (5x 0.5mm holes)
- **Impedance Control**: Standard 50-ohm single-ended / 90-ohm differential USB D+/D-

## 2. PCBA & SMT Assembly Requirements
- **SMT Sides**: Double-Sided SMT (Front gameplay controls SW4-SW17 + LCD socket J3; Rear active ICs U1-U4, passives, USB-C J1, battery connector J2)
- **Soldering Standard**: IPC-A-610 Class 2 / Lead-Free RoHS
- **Thermal Ground Pad Stencil**: Split ESP32-S3 center ground pad aperture into 4 windowpanes (70% coverage) to prevent module floating.
- **Inspection**: 100% Automated Optical Inspection (AOI) + X-Ray for QFN/LGA packages + IPC-D-356 Flying Probe / Bed of Nails E-Test.
"""
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"    Saved Lion Circuits manufacturing order specification to {spec_path}.")


def package_release():
    ensure_dirs()
    print(
        f"==> [8/8] Packaging Complete Lion Circuits Turnkey Release Bundle ({RELEASE_ZIP})..."
    )
    export_gerbers()
    export_drill()
    zip_gerbers()
    export_cpl()
    export_bom()
    export_d356()
    export_pdf()
    export_spec()

    with zipfile.ZipFile(RELEASE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(GERBERS_ZIP, arcname=os.path.basename(GERBERS_ZIP))
        for fname in [
            "cpl.csv",
            "bom.csv",
            f"{PROJECT_NAME}.d356",
            f"{PROJECT_NAME}_Schematic.pdf",
            f"{PROJECT_NAME}_PCB_Layers.pdf",
            "ORDER_SPEC.md",
        ]:
            fpath = os.path.join(BUILD_DIR, fname)
            if os.path.exists(fpath):
                zf.write(fpath, arcname=fname)

    print("======================================================================")
    print(f"RELEASE READY: {RELEASE_ZIP} ({os.path.getsize(RELEASE_ZIP) // 1024} KB)")
    print("======================================================================")


def main():
    parser = argparse.ArgumentParser(
        description="Export manufacturing release package for Lion Circuits"
    )
    parser.add_argument("--gerbers", action="store_true", help="Export RS-274X Gerbers")
    parser.add_argument(
        "--drill", action="store_true", help="Export NC Excellon drill files"
    )
    parser.add_argument(
        "--zip-gerbers", action="store_true", help="Zip Gerbers and drills"
    )
    parser.add_argument(
        "--cpl", action="store_true", help="Export pick-and-place centroid file"
    )
    parser.add_argument(
        "--bom", action="store_true", help="Export structured Bill of Materials"
    )
    parser.add_argument(
        "--d356", action="store_true", help="Export IPC-D-356 electrical test netlist"
    )
    parser.add_argument(
        "--pdf", action="store_true", help="Export schematic and PCB layer PDFs"
    )
    parser.add_argument(
        "--spec", action="store_true", help="Generate Lion Circuits ORDER_SPEC.md"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate complete manufacturing release bundle",
    )

    args = parser.parse_args()

    if args.all or not any(vars(args).values()):
        package_release()
    else:
        if args.gerbers:
            export_gerbers()
        if args.drill:
            export_drill()
        if args.zip_gerbers:
            zip_gerbers()
        if args.cpl:
            export_cpl()
        if args.bom:
            export_bom()
        if args.d356:
            export_d356()
        if args.pdf:
            export_pdf()
        if args.spec:
            export_spec()


if __name__ == "__main__":
    main()
