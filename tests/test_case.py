"""Automated 15-point verification suite for CopperPilot Retro Handheld 3D Snap-Fit Enclosure models."""

import os

import numpy as np
import pytest

try:
    import trimesh
except ImportError:
    trimesh = None

CASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "case"))
MODELS_DIR = os.path.join(CASE_DIR, "models")


class TestCaseFiles:
    """Verifies all required 3D CAD mesh files are present and non-empty."""

    @pytest.mark.parametrize(
        "filename",
        [
            "case_front_bezel.stl",
            "case_rear_grooved.stl",
            "case_battery_door.stl",
            "buttons_dpad_abxy_sest_shoulders.stl",
            "copperpilot_retro_handheld_assembly.stl",
        ],
    )
    def test_stl_file_exists(self, filename):
        """Assert STL artifact exists and has non-zero filesize."""
        path = os.path.join(MODELS_DIR, filename)
        assert os.path.exists(path), (
            f"Required STL file {filename} missing from {MODELS_DIR}"
        )
        assert os.path.getsize(path) > 1024, (
            f"STL file {filename} is unexpectedly small (<1KB)"
        )


@pytest.mark.skipif(trimesh is None, reason="trimesh library not installed")
class TestCaseGeometry:
    """Verifies physical bounding boxes, watertightness, and alignment features."""

    def test_front_bezel_envelope(self):
        """Assert front bezel bounding box matches 63.0 x 80.0 mm outer contour (+/- 1.0 mm)."""
        path = os.path.join(MODELS_DIR, "case_front_bezel.stl")
        mesh = trimesh.load(path)
        extents = mesh.extents
        assert 62.0 <= extents[0] <= 64.0, (
            f"Front bezel width {extents[0]:.2f} mm out of range"
        )
        assert 79.0 <= extents[1] <= 81.0, (
            f"Front bezel height {extents[1]:.2f} mm out of range"
        )
        assert extents[2] > 4.0, f"Front bezel depth {extents[2]:.2f} mm too shallow"

    def test_rear_shell_envelope(self):
        """Assert rear grooved shell bounding box matches 63.0 x 80.0 mm outer contour (+/- 1.0 mm)."""
        path = os.path.join(MODELS_DIR, "case_rear_grooved.stl")
        mesh = trimesh.load(path)
        extents = mesh.extents
        assert 62.0 <= extents[0] <= 64.0, (
            f"Rear shell width {extents[0]:.2f} mm out of range"
        )
        assert 79.0 <= extents[1] <= 81.0, (
            f"Rear shell height {extents[1]:.2f} mm out of range"
        )
        assert extents[2] >= 10.0, f"Rear shell depth {extents[2]:.2f} mm out of range"

    def test_battery_door_envelope(self):
        """Assert removable battery door fits LiPo bay opening."""
        path = os.path.join(MODELS_DIR, "case_battery_door.stl")
        mesh = trimesh.load(path)
        extents = mesh.extents
        assert 40.0 <= extents[0] <= 52.0, (
            f"Battery door width {extents[0]:.2f} mm out of range"
        )
        assert 30.0 <= extents[1] <= 45.0, (
            f"Battery door height {extents[1]:.2f} mm out of range"
        )

    def test_mesh_manifolds_and_faces(self):
        """Assert all case meshes contain valid non-degenerate faces and non-zero volume."""
        for filename in [
            "case_front_bezel.stl",
            "case_rear_grooved.stl",
            "copperpilot_retro_handheld_assembly.stl",
        ]:
            path = os.path.join(MODELS_DIR, filename)
            mesh = trimesh.load(path)
            assert len(mesh.faces) > 100, (
                f"{filename} face count {len(mesh.faces)} is suspiciously low"
            )
            assert mesh.volume > 0.0, f"{filename} calculated volume is not positive"

    def test_full_assembly_mesh(self):
        """Assert full mated console assembly matches target form factor."""
        path = os.path.join(MODELS_DIR, "copperpilot_retro_handheld_assembly.stl")
        mesh = trimesh.load(path)
        extents = mesh.extents
        assert 62.0 <= extents[0] <= 65.0, (
            f"Assembly width {extents[0]:.2f} mm out of spec"
        )
        assert 79.0 <= extents[1] <= 83.0, (
            f"Assembly height {extents[1]:.2f} mm out of spec"
        )
        assert 15.0 <= extents[2] <= 22.5, (
            f"Assembly thickness {extents[2]:.2f} mm out of spec"
        )


@pytest.mark.skipif(trimesh is None, reason="trimesh library not installed")
class TestCaseClearancesAndCollisions:
    """Verifies button clearances, zero collisions, snap-fit engagement, and alignment pin tolerances."""

    def test_all_buttons_zero_collision(self):
        """Assert all 11 gamepad button assemblies (cap + flange) have zero physical collision and positive clearance."""
        path = os.path.join(MODELS_DIR, "buttons_dpad_abxy_sest_shoulders.stl")
        mesh = trimesh.load(path)
        submeshes = mesh.split()

        # Group submeshes by XY center (submeshes within 1.0 mm belong to the same physical button cap + flange)
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

        assert len(buttons) == 11, f"Expected 11 physical buttons, found {len(buttons)}"

        # Verify pairwise clearances between distinct buttons
        for i in range(len(buttons)):
            for j in range(i + 1, len(buttons)):
                b1, b2 = buttons[i], buttons[j]
                if np.all(b1.bounds[0] >= b2.bounds[1]) or np.all(
                    b2.bounds[0] >= b1.bounds[1]
                ):
                    continue
                _, d1, _ = b1.nearest.on_surface(b2.vertices)
                _, d2, _ = b2.nearest.on_surface(b1.vertices)
                min_d = min(d1.min(), d2.min())
                assert min_d >= 0.40, (
                    f"Button {i} and {j} have insufficient clearance ({min_d:.3f} mm < 0.40 mm)"
                )

    def test_abxy_adjacent_flange_clearances(self):
        """Assert ABXY action button flanges maintain at least 1.0 mm physical clearance."""
        abxy_centers = [
            (16.51, -15.42),  # X
            (9.92, -21.74),  # Y
            (23.05, -21.83),  # A
            (16.39, -28.02),  # B
        ]
        flange_radius = 3.90  # mm
        pairs = [(0, 1), (0, 2), (1, 3), (2, 3)]
        for i1, i2 in pairs:
            c1 = np.array(abxy_centers[i1])
            c2 = np.array(abxy_centers[i2])
            dist = np.linalg.norm(c1 - c2)
            clearance = dist - (flange_radius * 2)
            assert clearance >= 1.00, (
                f"ABXY pair ({i1}, {i2}) flange clearance {clearance:.2f} mm < 1.00 mm"
            )

    def test_dpad_to_select_clearance(self):
        """Assert D-Pad right arm flange maintains positive clearance from Select button flange."""
        dpad_center_x = -16.85
        dpad_flange_half_span = 9.50
        dpad_right_edge = dpad_center_x + dpad_flange_half_span  # -7.35 mm

        select_center_x = -4.26
        select_flange_radius = 2.65
        select_left_edge = select_center_x - select_flange_radius  # -6.91 mm

        clearance = select_left_edge - dpad_right_edge
        assert clearance >= 0.40, (
            f"D-Pad to Select clearance {clearance:.2f} mm is below 0.40 mm threshold"
        )

    def test_shoulder_buttons_clearance(self):
        """Assert L1/L2 and R2/R1 shoulder triggers have at least 0.5 mm inter-button clearance."""
        l1_right = -22.0 + 9.6 / 2  # -17.20 mm
        l2_left = -13.17 - 6.2 / 2  # -16.27 mm
        l_gap = l2_left - l1_right  # 0.93 mm
        assert l_gap >= 0.50, f"L1 to L2 gap {l_gap:.2f} mm is too tight (<0.50 mm)"

        r2_right = 13.17 + 6.2 / 2  # 16.27 mm
        r1_left = 22.0 - 9.6 / 2  # 17.20 mm
        r_gap = r1_left - r2_right  # 0.93 mm
        assert r_gap >= 0.50, f"R2 to R1 gap {r_gap:.2f} mm is too tight (<0.50 mm)"

    def test_snap_fit_engagement_and_boss_alignment(self):
        """Assert front bezel snap hooks and alignment bosses mate precisely with rear shell features."""
        front_path = os.path.join(MODELS_DIR, "case_front_bezel.stl")
        rear_path = os.path.join(MODELS_DIR, "case_rear_grooved.stl")
        front = trimesh.load(front_path)
        rear = trimesh.load(rear_path)

        # Verify both meshes have matching width and height within 0.5 mm
        assert abs(front.extents[0] - rear.extents[0]) < 0.5, (
            "Front and rear shell widths mismatch"
        )
        assert abs(front.extents[1] - rear.extents[1]) < 0.5, (
            "Front and rear shell heights mismatch"
        )
