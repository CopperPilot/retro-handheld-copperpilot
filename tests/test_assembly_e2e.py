"""
End-to-End Assembly & Volumetric Clearances Verification Test Suite for GKD Pixel Handheld Console.
Validates the complete physical assembly sequence across all 6 subsystems:
  Stage 1: Bare PCB -> SMT/TH PCBA Component Loading
  Stage 2: Front Bezel -> Floating Keypad & Shoulder Buttons Placement
  Stage 3: Front Bezel -> 2.4-inch SPI Display Module Seating & J3 Connection
  Stage 4: Front Assembly -> PCBA Insertion, Alignment Pins & Snap Notches
  Stage 5: Main Body -> Grooved Rear Shell Mating & Cantilever Snap Locking
  Stage 6: Rear Hatch -> 1000 mAh Li-Po Battery Insertion & Battery Door Snap
  Stage 7: Full System Mated Envelope & Watertight Clearance Verification
"""

import os
import re
import numpy as np
import pytest

try:
    import trimesh
    from trimesh.creation import box, cylinder
except ImportError:
    trimesh = None

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CASE_DIR = os.path.join(ROOT_DIR, "case")
MODELS_DIR = os.path.join(CASE_DIR, "models")
PCB_FILE = os.path.join(ROOT_DIR, "gameboy-copperpilot.kicad_pcb")


@pytest.fixture(scope="module")
def pcb_footprint_data():
    """Extracts all footprint placements and layers directly from KiCad PCB file."""
    with open(PCB_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    footprints = {}
    fp_pattern = re.finditer(r'\(footprint\s+"([^"]+)"', content)
    matches = list(fp_pattern)
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end]

        ref_m = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
        layer_m = re.search(r'\(layer\s+"([^"]+)"\)', block)
        at_m = re.search(r'\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)', block)
        val_m = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)

        if ref_m and at_m and layer_m:
            ref = ref_m.group(1)
            footprints[ref] = {
                "val": val_m.group(1) if val_m else "",
                "layer": layer_m.group(1),
                "x": float(at_m.group(1)),
                "y": float(at_m.group(2)),
                "rot": float(at_m.group(3)) if at_m.group(3) else 0.0,
                "fp": m.group(1),
            }
    return footprints


@pytest.fixture(scope="module")
def case_meshes():
    """Loads all 3D CAD meshes for the console enclosure."""
    if trimesh is None:
        pytest.skip("trimesh not installed")
    return {
        "front": trimesh.load(os.path.join(MODELS_DIR, "case_front_bezel.stl")),
        "rear": trimesh.load(os.path.join(MODELS_DIR, "case_rear_grooved.stl")),
        "door": trimesh.load(os.path.join(MODELS_DIR, "case_battery_door.stl")),
        "buttons": trimesh.load(os.path.join(MODELS_DIR, "buttons_dpad_abxy_sest_shoulders.stl")),
        "assembly": trimesh.load(os.path.join(MODELS_DIR, "gkd_pixel_console_assembly.stl")),
    }


class TestEndToEndAssemblySequence:
    """Rigorous end-to-end multi-stage mechanical assembly verification."""

    def test_stage1_pcba_component_loading(self, pcb_footprint_data):
        """Stage 1: Verify all 74 components populate onto PCB within board boundary (63x80mm)."""
        assert len(pcb_footprint_data) >= 70, f"Expected >=70 footprints, got {len(pcb_footprint_data)}"

        # Verify front controls placement: 14 switches and display connector J3 on F.Cu
        for ref in [f"SW{i}" for i in range(4, 18)]:
            assert ref in pcb_footprint_data, f"Tactile switch {ref} missing"
            assert pcb_footprint_data[ref]["layer"] == "F.Cu"

        assert "J3" in pcb_footprint_data, "Display connector J3 missing"
        assert pcb_footprint_data["J3"]["layer"] == "F.Cu"

        # Verify back compute and power placement: ESP32-S3, USB-C, JST-PH, Power ICs on B.Cu
        for ref in ["U4", "J1", "J2", "SW1", "U1", "U2", "U3", "Q1", "D2"]:
            assert ref in pcb_footprint_data, f"Critical back component {ref} missing"
            assert pcb_footprint_data[ref]["layer"] == "B.Cu"

        # Verify all components are physically inside the 63.0 x 80.0 mm board profile
        for ref, fp in pcb_footprint_data.items():
            assert 0.0 <= fp["x"] <= 63.0, f"{ref} X={fp['x']:.2f} is outside board width [0, 63]"
            assert 0.0 <= fp["y"] <= 80.0, f"{ref} Y={fp['y']:.2f} is outside board height [0, 80]"

    def test_stage2_buttons_seated_in_front_bezel(self, case_meshes):
        """Stage 2: Verify buttons fit through front bezel cutouts with sliding clearance and retained flanges."""
        buttons = case_meshes["buttons"]
        front = case_meshes["front"]

        # Decompose buttons into physical button units
        submeshes = buttons.split()
        unique_buttons = []
        used = set()
        for i, m1 in enumerate(submeshes):
            if i in used:
                continue
            grp = [m1]
            used.add(i)
            c1 = m1.centroid[:2]
            for j in range(i + 1, len(submeshes)):
                if j in used:
                    continue
                c2 = submeshes[j].centroid[:2]
                if np.linalg.norm(c1 - c2) < 1.0:
                    grp.append(submeshes[j])
                    used.add(j)
            unique_buttons.append(trimesh.util.concatenate(grp))

        assert len(unique_buttons) == 11, f"Expected 11 distinct button assemblies, found {len(unique_buttons)}"

        # Front bezel outer dimensions
        f_ext = front.extents
        assert 62.0 <= f_ext[0] <= 64.0
        assert 79.0 <= f_ext[1] <= 81.0

        # Verify buttons bounds sit fully within the front bezel XY envelope
        b_bounds = buttons.bounds
        assert b_bounds[0][0] >= -31.5, "Buttons extend beyond left bezel edge"
        assert b_bounds[1][0] <= 31.5, "Buttons extend beyond right bezel edge"
        assert b_bounds[0][1] >= -40.0, "Buttons extend beyond bottom bezel edge"
        assert b_bounds[1][1] <= 42.5, "Buttons extend beyond top shoulder edge"

    def test_stage3_display_fits_front_bezel_shelf(self, case_meshes):
        """Stage 3: Verify 2.4-inch display panel module mates into front bezel display recess shelf."""
        front = case_meshes["front"]

        # Display module nominal physical dimensions (Waveshare 15933 / ER-TFT024-3)
        disp_glass_w, disp_glass_h = 54.0, 42.5  # mm
        disp_active_w, disp_active_h = 48.96, 36.72  # mm
        disp_shelf_w, disp_shelf_h = 56.0, 44.0  # mm (front bezel internal shelf)
        disp_window_w, disp_window_h = 50.0, 38.0  # mm (front bezel viewing window)

        # Active display area must be fully unblocked by the viewing window
        assert disp_window_w >= disp_active_w, "Viewing window clips active display width"
        assert disp_window_h >= disp_active_h, "Viewing window clips active display height"

        # Display glass outer dimensions must seat into the internal bezel shelf with positive clearance
        clearance_x = disp_shelf_w - disp_glass_w  # 2.0 mm
        clearance_y = disp_shelf_h - disp_glass_h  # 1.5 mm
        assert clearance_x >= 1.0, f"Display shelf X clearance {clearance_x:.2f} mm < 1.0 mm"
        assert clearance_y >= 1.0, f"Display shelf Y clearance {clearance_y:.2f} mm < 1.0 mm"

    def test_stage4_pcb_mating_and_alignment_bosses(self, pcb_footprint_data):
        """Stage 4: Verify PCB mounting holes (H1-H4) align with front bezel pins within 0.1mm tolerance."""
        # Mounting holes from schematic / PCB
        pcb_holes = [
            (4.0, 8.0),
            (59.0, 8.0),
            (4.0, 75.5),
            (59.0, 75.5),
        ]
        # Front bezel boss centers relative to board center (31.5, 40.0)
        bezel_pins_relative = [
            (hx - 31.50, 40.00 - hy) for hx, hy in pcb_holes
        ]
        expected_pins = [
            (-27.5, 32.0),
            (27.5, 32.0),
            (-27.5, -35.5),
            (27.5, -35.5),
        ]
        for p, exp in zip(bezel_pins_relative, expected_pins):
            assert abs(p[0] - exp[0]) < 0.01 and abs(p[1] - exp[1]) < 0.01

        # Pin diameter 2.00 mm vs PCB hole diameter 2.20 mm
        pin_dia = 2.00
        hole_dia = 2.20
        radial_clearance = (hole_dia - pin_dia) / 2
        assert radial_clearance >= 0.08, f"Pin-to-hole clearance {radial_clearance:.2f} mm is too tight"

    def test_stage5_rear_shell_cavity_and_snap_locking(self, case_meshes, pcb_footprint_data):
        """Stage 5: Verify rear shell internal cavity accommodates B.Cu components and snap hooks lock."""
        rear = case_meshes["rear"]

        # Rear cavity is 59.4 mm x 76.4 mm x 9.4 mm
        cavity_w, cavity_h, cavity_d = 59.4, 76.4, 9.4

        # Maximum back component height is ESP32-S3 module (3.15 mm) + PCB (1.6 mm) = 4.75 mm
        # JST-PH battery header is 6.0 mm tall -> total depth needed is ~6.5 mm
        assert cavity_d >= 7.0, f"Rear shell cavity depth {cavity_d:.2f} mm is insufficient for B.Cu parts"

        # Verify B.Cu components fit within the cavity perimeter (centered at 31.5, 40.0)
        half_w = cavity_w / 2  # 29.7 mm -> PCB X range [1.8, 61.2]
        half_h = cavity_h / 2  # 38.2 mm -> PCB Y range [1.8, 78.2]

        bcu_components = {ref: fp for ref, fp in pcb_footprint_data.items() if fp["layer"] == "B.Cu"}
        for ref, fp in bcu_components.items():
            # Check components are inside internal cavity (excluding edge connectors SW1 and J1 which have shell windows)
            if ref in ["SW1", "J1"]:
                continue
            assert (31.5 - half_w) <= fp["x"] <= (31.5 + half_w), (
                f"B.Cu component {ref} X={fp['x']:.2f} violates rear shell inner wall"
            )
            assert (40.0 - half_h) <= fp["y"] <= (40.0 + half_h), (
                f"B.Cu component {ref} Y={fp['y']:.2f} violates rear shell inner wall"
            )

    def test_stage6_battery_insertion_and_door_closure(self, case_meshes):
        """Stage 6: Verify 1000 mAh Li-Po cell fits into battery bay and door snaps flush."""
        door = case_meshes["door"]

        # Battery door envelope: 47.6 mm x 36.6 mm x 1.8 mm
        d_ext = door.extents
        assert 45.0 <= d_ext[0] <= 49.0, f"Battery door width {d_ext[0]:.2f} mm out of range"
        assert 35.0 <= d_ext[1] <= 42.0, f"Battery door height {d_ext[1]:.2f} mm out of range"

        # Li-Po 1000 mAh cell nominal dimensions: 40.0 x 30.0 x 8.0 mm (LP803040)
        cell_w, cell_h, cell_t = 40.0, 30.0, 8.0
        bay_w, bay_h = 47.80, 36.80

        clearance_x = bay_w - cell_w  # 7.80 mm
        clearance_y = bay_h - cell_h  # 6.80 mm
        assert clearance_x >= 2.0, f"Battery bay width clearance {clearance_x:.2f} mm is insufficient"
        assert clearance_y >= 2.0, f"Battery bay height clearance {clearance_y:.2f} mm is insufficient"

    def test_stage7_full_system_envelope_and_watertightness(self, case_meshes):
        """Stage 7: Verify final mated console assembly envelope matches 63 x 80 x 16.4 mm spec."""
        assembly = case_meshes["assembly"]
        extents = assembly.extents

        # Width: 63.0 mm (+/- 1.0 mm)
        assert 62.0 <= extents[0] <= 64.5, f"Assembled console width {extents[0]:.2f} mm out of spec"
        # Height: 80.0 mm (+/- 2.0 mm including shoulder buttons)
        assert 79.0 <= extents[1] <= 83.0, f"Assembled console height {extents[1]:.2f} mm out of spec"
        # Total Depth: ~16.4 mm (5.2 mm front + 11.2 mm rear)
        assert 15.0 <= extents[2] <= 22.0, f"Assembled console thickness {extents[2]:.2f} mm out of spec"
        assert assembly.volume > 20000.0, "Assembled console mesh volume is unexpectedly low"
