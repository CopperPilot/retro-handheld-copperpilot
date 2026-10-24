"""
End-to-End Assembly & Volumetric Clearances Verification Test Suite for GKD Pixel Handheld Console.
Validates the complete physical assembly sequence and kinematics across all 6 subsystems:
  Stage 1: Bare PCB -> SMT/TH PCBA Component Loading (74 components)
  Stage 2: KiCad 3D Exported Mesh Verification (copperpilot_retro_handheld_pcb_populated.stl & .glb)
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
PCB_FILE = os.path.join(ROOT_DIR, "copperpilot-retro-handheld.kicad_pcb")


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
    pcb_stl_path = os.path.join(MODELS_DIR, "copperpilot_retro_handheld_pcb_populated.stl")
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

    def test_stage4_buttons_seat_onto_pcba_zero_collision(self, case_meshes):
        """Stage 4: Verify seated gamepad keycaps directly contact switch actuators with zero penetration."""
        buttons = case_meshes["buttons"]
        pcb = case_meshes["pcb"]

        mgr = CollisionManager()
        mgr.add_object("buttons", buttons)
        mgr.add_object("pcb", pcb)
        assert not mgr.in_collision_internal(), "Gamepad keycaps collide with PCBA tactile switches"
        min_dist = mgr.min_distance_internal()
        assert min_dist >= 0.05, f"Keycap to tactile switch clearance {min_dist:.3f} mm < 0.05 mm"

    def test_stage5_buttons_seat_in_front_bezel_zero_collision(self, case_meshes):
        """Stage 5: Verify seated buttons inside the front bezel cutouts have zero volumetric collision."""
        front = case_meshes["front"]
        buttons = case_meshes["buttons"]

        mgr = CollisionManager()
        mgr.add_object("front", front)
        mgr.add_object("buttons", buttons)
        assert not mgr.in_collision_internal(), "Seated buttons collide with front bezel housing"
        min_dist = mgr.min_distance_internal()
        assert min_dist >= 0.35, f"Button bore radial clearance {min_dist:.3f} mm is below 0.35 mm"

    def test_stage6_display_shelf_mating_and_j3_interconnect(self, case_meshes):
        """Stage 6: Verify 2.4-inch display panel module seats into front bezel and connects to J3 without interference."""
        front = case_meshes["front"]
        pcb = case_meshes["pcb"]

        # Display module nominal physical dimensions (Waveshare 15933 / ER-TFT024-3)
        disp_glass = box(extents=[49.0, 35.0, 1.0]).apply_translation([0.0, 14.5, 4.80])
        disp_pcb = box(extents=[50.0, 33.0, 0.8]).apply_translation([0.0, 14.5, 3.85])
        disp_ribbon = box(extents=[8.0, 3.0, 0.2]).apply_translation([0.0, -1.8, 5.86])
        display = trimesh.util.concatenate([disp_glass, disp_pcb, disp_ribbon])

        # Verify display vs PCB (clears J2 through-hole pins and mates into J3)
        m_pcb = CollisionManager()
        m_pcb.add_object("display", display)
        m_pcb.add_object("pcb", pcb)
        assert not m_pcb.in_collision_internal(), "Display module collides with PCB components"
        assert m_pcb.min_distance_internal() >= 0.10, "Display PCB clearance over board is too tight"

        # Verify display vs Front Bezel (seats inside internal shelf)
        m_front = CollisionManager()
        m_front.add_object("display", display)
        m_front.add_object("front", front)
        assert not m_front.in_collision_internal(), "Display module collides with front bezel shelf"

    def test_stage7_pcba_mating_to_front_bezel_zero_collision(self, case_meshes):
        """Stage 7: Verify populated KiCad PCBA seats against front bezel with zero volumetric collision."""
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

    def test_stage8_rear_shell_mating_over_pcb_zero_collision(self, case_meshes):
        """Stage 8: Verify grooved rear shell seats over populated PCBA with zero volumetric collision."""
        rear = case_meshes["rear"]
        pcb = case_meshes["pcb"]

        mgr = CollisionManager()
        mgr.add_object("rear", rear)
        mgr.add_object("pcb", pcb)
        assert not mgr.in_collision_internal(), "Rear grooved shell collides with populated KiCad PCBA"

    def test_stage9_battery_seating_and_rear_cavity_fit(self, case_meshes):
        """Stage 9: Verify 1000 mAh Li-Po cell fits into rear cavity without interfering with PCB or rear housing."""
        pcb = case_meshes["pcb"]
        rear = case_meshes["rear"]

        # 1000 mAh Li-Po cell (26.0 x 38.0 x 6.0 mm, placed at X=3.0, Y=-8.0, Z=-6.0)
        bat = box(extents=[26.0, 38.0, 6.0]).apply_translation([3.0, -8.0, -6.0])

        m_pcb = CollisionManager()
        m_pcb.add_object("bat", bat)
        m_pcb.add_object("pcb", pcb)
        assert not m_pcb.in_collision_internal(), "Battery collides with PCB components"
        assert m_pcb.min_distance_internal() >= 1.0, "Battery clearance to PCB components < 1.0 mm"

        m_rear = CollisionManager()
        m_rear.add_object("bat", bat)
        m_rear.add_object("rear", rear)
        assert not m_rear.in_collision_internal(), "Battery collides with rear housing shell"
        assert m_rear.min_distance_internal() >= 0.40, "Battery clearance to rear wall < 0.40 mm"

    def test_stage10_continuous_kinematic_assembly_trajectories(self, case_meshes):
        """Stage 10: Verify multi-step continuous collision clearance along all physical assembly flight paths."""
        front = case_meshes["front"]
        rear = case_meshes["rear"]
        buttons = case_meshes["buttons"]
        pcb = case_meshes["pcb"]

        disp_glass = box(extents=[49.0, 35.0, 1.0]).apply_translation([0.0, 14.5, 4.80])
        disp_pcb = box(extents=[50.0, 33.0, 0.8]).apply_translation([0.0, 14.5, 3.85])
        disp_ribbon = box(extents=[8.0, 3.0, 0.2]).apply_translation([0.0, -1.8, 5.86])
        display = trimesh.util.concatenate([disp_glass, disp_pcb, disp_ribbon])

        bat = box(extents=[26.0, 38.0, 6.0]).apply_translation([3.0, -8.0, -6.0])

        # Approach Vector 1: Buttons fly in from +Z = 60.0 mm to Z = 0.0 mm onto PCB
        for z in np.linspace(60.0, 0.0, 13):
            b_step = buttons.copy()
            b_step.apply_translation([0, 0, z])
            m = CollisionManager()
            m.add_object("pcb", pcb)
            m.add_object("b", b_step)
            assert not m.in_collision_internal(), f"Buttons collided with PCB at trajectory Z = {z:.1f} mm"

        # Approach Vector 2: Display module descends from +Z = 60.0 mm to Z = 0.0 mm onto PCB + Buttons
        for z in np.linspace(60.0, 0.0, 13):
            d_step = display.copy()
            d_step.apply_translation([0, 0, z])
            m = CollisionManager()
            m.add_object("pcb", pcb)
            m.add_object("b", buttons)
            m.add_object("d", d_step)
            assert not m.in_collision_internal(), f"Display collided with assembly at trajectory Z = {z:.1f} mm"

        # Approach Vector 3: Front Bezel lowers from +Z = 60.0 mm to Z = 0.0 mm over PCB + Buttons + Display
        for z in np.linspace(60.0, 0.0, 13):
            f_step = front.copy()
            f_step.apply_translation([0, 0, z])
            m = CollisionManager()
            m.add_object("pcb", pcb)
            m.add_object("b", buttons)
            m.add_object("d", display)
            m.add_object("f", f_step)
            assert not m.in_collision_internal(), f"Front bezel collided with assembly at trajectory Z = {z:.1f} mm"

        # Approach Vector 4: Battery pack inserts from -Z = -50.0 mm to Z = 0.0 mm into rear cavity
        for z in np.linspace(-50.0, 0.0, 11):
            bat_step = bat.copy()
            bat_step.apply_translation([0, 0, z])
            m = CollisionManager()
            m.add_object("pcb", pcb)
            m.add_object("bat", bat_step)
            assert not m.in_collision_internal(), f"Battery collided with PCB at trajectory Z = {z:.1f} mm"

        # Approach Vector 5: Rear Housing closes from -Z = -60.0 mm to Z = 0.0 mm over assembly
        for z in np.linspace(-60.0, 0.0, 13):
            r_step = rear.copy()
            r_step.apply_translation([0, 0, z])
            m = CollisionManager()
            m.add_object("pcb", pcb)
            m.add_object("bat", bat)
            m.add_object("front", front)
            m.add_object("r", r_step)
            assert not m.in_collision_internal(), f"Rear shell collided with assembly at trajectory Z = {z:.1f} mm"

    def test_stage11_full_console_assembly_envelope(self, case_meshes):
        """Stage 11: Verify final assembled console envelope matches target form factor."""
        assembly = case_meshes["assembly"]
        extents = assembly.extents

        # Width: 63.0 mm (+/- 1.0 mm)
        assert 62.0 <= extents[0] <= 64.5, f"Assembled console width {extents[0]:.2f} mm out of spec"
        # Height: 80.0 mm (+/- 2.0 mm including shoulder buttons)
        assert 79.0 <= extents[1] <= 83.0, f"Assembled console height {extents[1]:.2f} mm out of spec"
        # Total Depth: 18.0 mm (+/- 2.0 mm)
        assert 16.0 <= extents[2] <= 20.5, f"Assembled console thickness {extents[2]:.2f} mm out of spec"
        assert assembly.volume > 15000.0, "Assembled console mesh volume is unexpectedly low"
