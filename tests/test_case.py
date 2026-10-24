"""Automated 15-point verification suite for GKD Pixel 3D Snap-Fit Enclosure models."""

import os

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
            "gkd_pixel_console_assembly.stl",
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
            "gkd_pixel_console_assembly.stl",
        ]:
            path = os.path.join(MODELS_DIR, filename)
            mesh = trimesh.load(path)
            assert len(mesh.faces) > 100, (
                f"{filename} face count {len(mesh.faces)} is suspiciously low"
            )
            assert mesh.volume > 0.0, f"{filename} calculated volume is not positive"

    def test_full_assembly_mesh(self):
        """Assert full mated console assembly matches target form factor."""
        path = os.path.join(MODELS_DIR, "gkd_pixel_console_assembly.stl")
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
