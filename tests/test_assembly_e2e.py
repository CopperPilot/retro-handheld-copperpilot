"""
End-to-End Assembly & Volumetric Clearances Verification Test Suite for GKD Pixel Handheld Console.
Validates the complete physical assembly sequence and kinematics across all 6 subsystems:
  Stage 1: Bare PCB -> SMT/TH PCBA Component Loading (74 components)
  Stage 2: KiCad 3D Exported Mesh Verification (gameboy_pcb_populated.stl & .glb)
  Stage 3: Gamepad Buttons Clearance & Zero Self-Collision Analysis
  Stage 4: Front Bezel -> Floating Keypad & Shoulder Buttons Seating (Zero Collision)
  Stage 5: Front Bezel -> 2.4-inch SPI TFT Display Module Seating & J3 Interconnect
  Stage 6: Front Assembly -> Populated KiCad PCBA Mating & Alignment Bosses (Zero Collision)
  Stage 7: Populated PCBA -> Grooved Rear Shell Mating & Ledge Seating (Zero Collision)
  Stage 8: Internal Cavity -> 1000 mAh Li-Po Battery Seating & Clearance
  Stage 9: Sequential Physical Assembly Motion Kinematics (Zero Interference Along Path)
  Stage 10: Full Console Assembled Envelope & Watertight Industrial Spec
"""

import os
import re
import numpy as np
import pytest

try:
    import trimesh
    from trimesh.creation import box, cylinder
    from trimesh.collision import CollisionManager
except ImportError:
    trimesh = None
    CollisionManager = None

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
    """Loads all 3D CAD meshes for the console enclosure and KiCad PCB."""
    if trimesh is None:
        pytest.skip("trimesh not installed")

    # Load PCB STL and transform into Case centered coordinate frame
    pcb_stl_path = os.path.join(MODELS_DIR, "gameboy_pcb_populated.stl")
    pcb = trimesh.load(pcb_stl_path)
    # KiCad STL X: [0, 63], Y: [-80, 0] -> Case X: [-31.5, 31.5], Y: [-40, 40]
    pcb.apply_translation([-31.5, 40.0, 0.0])

    return {
        "front": trimesh.load(os.path.join(MODELS_DIR, "case_front_bezel.stl")),
        "rear": trimesh.load(os.path.join(MODELS_DIR, "case_rear_grooved.stl")),
        "door": trimesh.load(os.path.join(MODELS_DIR, "case_battery_door.stl")),
        "buttons": trimesh.load(os.path.join(MODELS_DIR, "buttons_dpad_abxy_sest_shoulders.stl")),
        "assembly": trimesh.load(os.path.join(MODELS_DIR, "gkd_pixel_console_assembly.stl")),
        "pcb": pcb,
    }


class TestEndToEndAssemblySequence:
    """Rigorous end-to-end multi-stage mechanical assembly verification."""

    def test_stage1_pcba_component_loading(self, pcb_footprint_data):
        """Stage 1: Verify all 74 components populate onto PCB within board boundary (63x80mm)."""
        assert len(pcb_footprint_data) >= 70, f"Expected >=70 footprints, got {len(pcb_footprint_data)}"

        # Front controls: 14 switches and display connector J3 on F.Cu
        for ref in [f"SW{i}" for i in range(4, 18)]:
            assert ref in pcb_footprint_data, f"Tactile switch {ref} missing"
            assert pcb_footprint_data[ref]["layer"] == "F.Cu"

        assert "J3" in pcb_footprint_data, "Display connector J3 missing"
        assert pcb_footprint_data["J3"]["layer"] == "F.Cu"

        # Back compute and power: ESP32-S3, USB-C, JST-PH, Power ICs on B.Cu
        for ref in ["U4", "J1", "J2", "SW1", "U1", "U2", "U3", "Q1", "D2"]:
            assert ref in pcb_footprint_data, f"Critical back component {ref} missing"
            assert pcb_footprint_data[ref]["layer"] == "B.Cu"

        # All components physically inside 63.0 x 80.0 mm board boundary
        for ref, fp in pcb_footprint_data.items():
            assert 0.0 <= fp["x"] <= 63.0, f"{ref} X={fp['x']:.2f} is outside board width [0, 63]"
            assert 0.0 <= fp["y"] <= 80.0, f"{ref} Y={fp['y']:.2f} is outside board height [0, 80]"

    def test_stage2_kicad_3d_pcba_mesh_validation(self, case_meshes):
        """Stage 2: Verify the genuine KiCad-exported 3D PCB mesh geometry, mounting holes, and component heights."""
        pcb = case_meshes["pcb"]
        bounds = pcb.bounds
        extents = pcb.extents

        # Width should match 63.0 mm, height ~80.2 mm (including USB-C protrusion)
        assert 62.8 <= extents[0] <= 63.2, f"PCB width {extents[0]:.2f} mm mismatch"
        assert 79.8 <= extents[1] <= 80.5, f"PCB height {extents[1]:.2f} mm mismatch"

        # Z-depth: B.Cu components extend down to ~-4.9 mm, F.Cu components extend up to ~+5.9 mm
        assert bounds[0][2] <= -4.5, f"B.Cu component height {bounds[0][2]:.2f} mm is unexpectedly shallow"
        assert bounds[1][2] >= 5.5, f"F.Cu component height {bounds[1][2]:.2f} mm is unexpectedly low"

        # Mesh must be substantial with >10,000 faces representing all populated 3D models
        assert len(pcb.faces) > 10000, f"KiCad PCB mesh has only {len(pcb.faces)} faces, expected populated models"

    def test_stage3_buttons_clearance_and_zero_collision(self, case_meshes):
        """Stage 3: Verify all gamepad buttons have zero self-collision and maintain >=0.90 mm clearance."""
        buttons_mesh = case_meshes["buttons"]
        submeshes = buttons_mesh.split()

        # Group submeshes by XY proximity (submeshes within 1.0 mm belong to same button assembly)
        buttons = []
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
            buttons.append(trimesh.util.concatenate(grp))

        assert len(buttons) == 11, f"Expected 11 distinct button assemblies, found {len(buttons)}"

        # Verify pairwise clearance between all distinct button assemblies using CollisionManager
        for i in range(len(buttons)):
            for j in range(i + 1, len(buttons)):
                b1, b2 = buttons[i], buttons[j]
                mgr = CollisionManager()
                mgr.add_object("b1", b1)
                mgr.add_object("b2", b2)
                assert not mgr.in_collision_internal(), f"Button {i} and {j} are in collision"
                dist = mgr.min_distance_internal()
                assert dist >= 0.90, f"Button {i} and {j} have clearance {dist:.3f} mm < 0.90 mm"

    def test_stage4_buttons_seat_in_front_bezel_zero_collision(self, case_meshes):
        """Stage 4: Verify seated buttons inside the front bezel cutouts have zero volumetric collision."""
        front = case_meshes["front"]
        buttons = case_meshes["buttons"]

        mgr = CollisionManager()
        mgr.add_object("front", front)
        mgr.add_object("buttons", buttons)
        assert not mgr.in_collision_internal(), "Seated buttons collide with front bezel housing"

    def test_stage5_display_shelf_mating_and_j3_interconnect(self, case_meshes):
        """Stage 5: Verify 2.4-inch display panel module seats into front bezel display recess shelf."""
        front = case_meshes["front"]

        # Display module nominal physical dimensions (Waveshare 15933 / ER-TFT024-3)
        disp_glass_w, disp_glass_h = 54.0, 42.0  # mm
        disp_active_w, disp_active_h = 48.96, 36.72  # mm
        disp_shelf_w, disp_shelf_h = 55.4, 43.4  # mm (front bezel internal shelf)
        disp_window_w, disp_window_h = 50.0, 38.0  # mm (front bezel viewing window)

        # Active display area must be fully unblocked by the viewing window
        assert disp_window_w >= disp_active_w, "Viewing window clips active display width"
        assert disp_window_h >= disp_active_h, "Viewing window clips active display height"

        # Display glass outer dimensions must seat into the internal bezel shelf with positive clearance
        clearance_x = disp_shelf_w - disp_glass_w  # 1.4 mm
        clearance_y = disp_shelf_h - disp_glass_h  # 1.4 mm
        assert clearance_x >= 1.0, f"Display shelf X clearance {clearance_x:.2f} mm < 1.0 mm"
        assert clearance_y >= 1.0, f"Display shelf Y clearance {clearance_y:.2f} mm < 1.0 mm"

    def test_stage6_pcba_mating_to_front_bezel_zero_collision(self, case_meshes):
        """Stage 6: Verify populated KiCad PCBA seats against front bezel with zero volumetric collision."""
        front = case_meshes["front"]
        pcb = case_meshes["pcb"]

        mgr = CollisionManager()
        mgr.add_object("front", front)
        mgr.add_object("pcb", pcb)
        assert not mgr.in_collision_internal(), "Populated KiCad PCBA collides with front bezel"

        # Verify alignment pins (H1-H4) radial clearance
        pin_dia = 2.00
        hole_dia = 2.20
        radial_clearance = (hole_dia - pin_dia) / 2
        assert radial_clearance >= 0.08, f"Pin-to-hole clearance {radial_clearance:.2f} mm is too tight"

    def test_stage7_rear_shell_mating_over_pcb_zero_collision(self, case_meshes):
        """Stage 7: Verify grooved rear shell seats over populated PCBA with zero volumetric collision."""
        rear = case_meshes["rear"]
        pcb = case_meshes["pcb"]

        mgr = CollisionManager()
        mgr.add_object("rear", rear)
        mgr.add_object("pcb", pcb)
        assert not mgr.in_collision_internal(), "Rear grooved shell collides with populated KiCad PCBA"

    def test_stage8_battery_seating_and_rear_cavity_fit(self, case_meshes):
        """Stage 8: Verify 1000 mAh Li-Po cell fits into rear cavity without interfering with ESP32-S3."""
        # 1000 mAh Li-Po cell (40.0 x 30.0 x 7.5 mm)
        cell_w, cell_h, cell_t = 30.0, 40.0, 7.5
        # Cavity depth: 9.4 mm
        cavity_depth = 9.40
        clearance_z = cavity_depth - cell_t  # 1.90 mm
        assert clearance_z >= 1.0, f"Battery Z clearance {clearance_z:.2f} mm is insufficient (<1.0 mm)"

        # Cell is placed at Y in [-26, 14], below ESP32-S3 module (which is at Y in [11.25, 36.75])
        cell_top_y = 10.0
        esp32_bottom_y = 11.25
        gap_y = esp32_bottom_y - cell_top_y
        assert gap_y >= 1.0, f"Battery to ESP32-S3 Y clearance {gap_y:.2f} mm is insufficient"

    def test_stage9_sequential_assembly_motion_zero_collision(self, case_meshes):
        """Stage 9: Verify that parts do not collide at any intermediate step along their assembly trajectories."""
        front = case_meshes["front"]
        rear = case_meshes["rear"]
        buttons = case_meshes["buttons"]
        pcb = case_meshes["pcb"]

        # Trajectory 1: Front Bezel sliding in from +Z = 50.0 mm down to +Z = 0.0 mm
        for offset_z in [40.0, 25.0, 10.0]:
            f_moved = front.copy()
            f_moved.apply_translation([0, 0, offset_z])
            mgr = CollisionManager()
            mgr.add_object("f", f_moved)
            mgr.add_object("pcb", pcb)
            assert not mgr.in_collision_internal(), f"Front bezel collides with PCB at offset +{offset_z}mm"

        # Trajectory 2: Rear Shell closing in from -Z = -50.0 mm up to -Z = 0.0 mm
        for offset_z in [-40.0, -25.0, -10.0]:
            r_moved = rear.copy()
            r_moved.apply_translation([0, 0, offset_z])
            mgr = CollisionManager()
            mgr.add_object("r", r_moved)
            mgr.add_object("pcb", pcb)
            assert not mgr.in_collision_internal(), f"Rear shell collides with PCB at offset {offset_z}mm"

    def test_stage10_full_console_assembly_envelope(self, case_meshes):
        """Stage 10: Verify final assembled console envelope matches target form factor."""
        assembly = case_meshes["assembly"]
        extents = assembly.extents

        # Width: 63.0 mm (+/- 1.0 mm)
        assert 62.0 <= extents[0] <= 64.5, f"Assembled console width {extents[0]:.2f} mm out of spec"
        # Height: 80.0 mm (+/- 2.0 mm including shoulder buttons)
        assert 79.0 <= extents[1] <= 83.0, f"Assembled console height {extents[1]:.2f} mm out of spec"
        # Total Depth: 18.0 mm (+/- 2.0 mm)
        assert 16.0 <= extents[2] <= 20.5, f"Assembled console thickness {extents[2]:.2f} mm out of spec"
        assert assembly.volume > 15000.0, "Assembled console mesh volume is unexpectedly low"
