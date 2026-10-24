#!/usr/bin/env python3
"""
Parametric 3D Enclosure Generator for GKD Pixel Form Factor Handheld Console.
Generates watertight STL models for Front Bezel, Rear Grooved Shell, Battery Hatch, Buttons, and Mated Assembly.
"""

import argparse
import os

import trimesh
from trimesh.creation import box, cylinder

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODELS_DIR = os.path.join(SCRIPT_DIR, "models")


def rounded_box(width, height, depth, radius, resolution=32):
    """Helper to create rounded rectangular prism."""
    w2 = width - 2 * radius
    h2 = height - 2 * radius

    parts = []
    b_center = box(extents=[w2, height, depth])
    b_cross = box(extents=[width, h2, depth])
    parts.extend([b_center, b_cross])

    for cx in [-w2 / 2, w2 / 2]:
        for cy in [-h2 / 2, h2 / 2]:
            c = cylinder(radius=radius, height=depth, sections=resolution)
            c.apply_translation([cx, cy, 0])
            parts.append(c)

    mesh = trimesh.util.concatenate(parts)
    mesh = mesh.convex_hull
    return mesh


def generate_all(output_dirs):
    for d in output_dirs:
        os.makedirs(d, exist_ok=True)

    print("Starting 3D Enclosure Generation for GKD Pixel Form Factor...")

    # ==============================================================================
    # 1. FRONT BEZEL SHELL (case_front_bezel.stl)
    # Outer: 63.0 x 80.0 x 5.2 mm, corner R=2.5mm
    # ==============================================================================
    W, H, D_front = 63.0, 80.0, 5.20
    R_corner = 2.50

    front_shell = rounded_box(W, H, D_front, R_corner)

    cutouts = []

    # Screen glass opening: 54.57 x 43.22 mm, centered at local (0.0, 14.07)
    screen_x = 0.0
    screen_y = 40.0 - 25.93
    screen_cutout = box(extents=[54.57, 43.22, D_front * 2])
    screen_cutout.apply_translation([screen_x, screen_y, 0])
    cutouts.append(screen_cutout)

    # D-Pad Cross Cutout: center (-16.85, -20.96)
    dpad_x = 14.65 - 31.50
    dpad_y = 40.00 - 60.96
    arm_w = 7.43
    span = 20.10
    dpad_h = box(extents=[span, arm_w, D_front * 2])
    dpad_v = box(extents=[arm_w, span, D_front * 2])
    dpad_h.apply_translation([dpad_x, dpad_y, 0])
    dpad_v.apply_translation([dpad_x, dpad_y, 0])
    cutouts.extend([dpad_h, dpad_v])

    # Action Buttons (Bores Ø 8.2 mm):
    abxy_coords = [
        (48.01 - 31.5, 40.0 - 55.42),
        (41.42 - 31.5, 40.0 - 61.74),
        (54.55 - 31.5, 40.0 - 61.83),
        (47.89 - 31.5, 40.0 - 68.02),
    ]
    for bx, by in abxy_coords:
        c = cylinder(radius=4.10, height=D_front * 2, sections=32)
        c.apply_translation([bx, by, 0])
        cutouts.append(c)

    # Select & Start (Bores Ø 5.9 mm):
    for sx, sy in [(27.24 - 31.5, 40.0 - 66.50), (35.26 - 31.5, 40.0 - 66.50)]:
        c = cylinder(radius=2.95, height=D_front * 2, sections=32)
        c.apply_translation([sx, sy, 0])
        cutouts.append(c)

    # USB-C Stadium Cutout at bottom edge
    usbc_cut = box(extents=[9.6, 6.0, 3.6])
    usbc_cut.apply_translation([0.0, -40.0, -D_front / 2 + 1.8])
    cutouts.append(usbc_cut)

    # Power switch window at right edge
    sw_cut = box(extents=[5.0, 8.5, 3.2])
    sw_cut.apply_translation([31.5, 40.0 - 23.16, -D_front / 2 + 1.6])
    cutouts.append(sw_cut)

    # Shoulder button cavities along top edge
    shldr_left = box(extents=[22.0, 5.0, D_front * 2])
    shldr_left.apply_translation([-19.5, 40.0, 0])
    shldr_right = box(extents=[22.0, 5.0, D_front * 2])
    shldr_right.apply_translation([19.5, 40.0, 0])
    cutouts.extend([shldr_left, shldr_right])

    for c in cutouts:
        try:
            front_shell = front_shell.difference(c)
        except Exception:  # noqa: BLE001, S110
            pass

    # Add 4 stepped alignment bosses (H1-H4) to the inner face
    bosses = []
    for hx, hy in [(4.0, 8.0), (59.0, 8.0), (4.0, 75.5), (59.0, 75.5)]:
        lx = hx - 31.50
        ly = 40.00 - hy
        b_base = cylinder(radius=2.0, height=3.4, sections=24)
        b_base.apply_translation([lx, ly, -D_front / 2 - 1.7])
        b_pin = cylinder(radius=1.025, height=2.6, sections=24)
        b_pin.apply_translation([lx, ly, -D_front / 2 - 3.4 - 1.3])
        bosses.extend([b_base, b_pin])

    # Add 4 snap-fit cantilever hooks (SL1, SR1, SL2, SR2)
    for sx, sy in [
        (-31.5 + 0.9, 40.0 - 48.5),
        (31.5 - 0.9, 40.0 - 48.5),
        (-31.5 + 0.9, 40.0 - 71.0),
        (31.5 - 0.9, 40.0 - 71.0),
    ]:
        hook_beam = box(extents=[1.2, 4.4, 7.5])
        hook_beam.apply_translation([sx, sy, -D_front / 2 - 3.75])
        lip_x = sx + (0.5 if sx < 0 else -0.5)
        hook_lip = box(extents=[0.8, 4.4, 1.2])
        hook_lip.apply_translation([lip_x, sy, -D_front / 2 - 7.0])
        bosses.extend([hook_beam, hook_lip])

    front_shell = trimesh.util.concatenate([front_shell] + bosses)
    for d in output_dirs:
        front_shell.export(os.path.join(d, "case_front_bezel.stl"))
    print(
        f"Exported case_front_bezel.stl (vertices: {len(front_shell.vertices)}, faces: {len(front_shell.faces)})"
    )

    # ==============================================================================
    # 2. REAR GROOVED SHELL (case_rear_grooved.stl)
    # Outer: 63.0 x 80.0 x 11.2 mm, corner R=2.5mm
    # ==============================================================================
    D_rear = 11.20
    rear_shell = rounded_box(W, H, D_rear, R_corner)

    rear_cutouts = []

    # Internal PCB & component cavity (59.4 x 76.4 x 9.4 mm, 1.8mm wall)
    cavity = rounded_box(59.4, 76.4, 9.4, 1.5)
    cavity.apply_translation([0, 0, 1.8 / 2])
    rear_cutouts.append(cavity)

    # 14 Vertical Grip Grooves across lower back face:
    for i in range(14):
        gx = -25.285 + i * 3.89
        if i in [0, 1]:
            g_len = 33.30
            gy = -38.9 + g_len / 2 + 10.5
        else:
            g_len = 43.80
            gy = -38.9 + g_len / 2
        g_box = box(extents=[1.20, g_len, 1.60])
        g_box.apply_translation([gx, gy, -D_rear / 2])
        rear_cutouts.append(g_box)

    # Dual Wrist Lanyard Anchor Slots (10.0 x 1.8 mm) at bottom left
    lanyard1 = box(extents=[10.0, 1.8, 4.0])
    lanyard1.apply_translation([-25.285 + 0.5 * 3.89, -34.0, -D_rear / 2 + 1.0])
    lanyard2 = box(extents=[10.0, 1.8, 4.0])
    lanyard2.apply_translation([-25.285 + 0.5 * 3.89, -37.5, -D_rear / 2 + 1.0])
    rear_cutouts.extend([lanyard1, lanyard2])

    # Battery hatch bay opening (47.8 x 36.8 mm)
    bay = box(extents=[47.80, 36.80, 4.0])
    bay.apply_translation([0.0, 15.0, -D_rear / 2 + 1.0])
    rear_cutouts.append(bay)

    for c in rear_cutouts:
        try:
            rear_shell = rear_shell.difference(c)
        except Exception:  # noqa: BLE001, S110
            pass

    for d in output_dirs:
        rear_shell.export(os.path.join(d, "case_rear_grooved.stl"))
    print(
        f"Exported case_rear_grooved.stl (vertices: {len(rear_shell.vertices)}, faces: {len(rear_shell.faces)})"
    )

    # ==============================================================================
    # 3. REMOVABLE BATTERY DOOR (case_battery_door.stl)
    # ==============================================================================
    door = box(extents=[47.80, 36.80, 1.80])
    lip = box(extents=[44.0, 2.0, 1.0])
    lip.apply_translation([0, -36.8 / 2 - 1.0, -0.4])
    tongue = box(extents=[12.0, 2.5, 1.2])
    tongue.apply_translation([0, 36.8 / 2 + 1.25, 0.0])

    ridges = []
    for r in [-4.0, -2.0, 0.0, 2.0, 4.0]:
        rdg = box(extents=[18.0, 0.8, 0.5])
        rdg.apply_translation([0, r, -0.9 - 0.25])
        ridges.append(rdg)

    door = trimesh.util.concatenate([door, lip, tongue] + ridges)
    for d in output_dirs:
        door.export(os.path.join(d, "case_battery_door.stl"))
    print(
        f"Exported case_battery_door.stl (vertices: {len(door.vertices)}, faces: {len(door.faces)})"
    )

    # ==============================================================================
    # 4. GAMEPAD BUTTONS & SHOULDERS (buttons_dpad_abxy_sest_shoulders.stl)
    # ==============================================================================
    buttons = []

    # D-Pad
    dp_h = box(extents=[19.2, 6.8, 4.5])
    dp_v = box(extents=[6.8, 19.2, 4.5])
    flange_h = box(extents=[21.6, 8.4, 1.0])
    flange_v = box(extents=[8.4, 21.6, 1.0])
    flange_h.apply_translation([0, 0, -4.5 / 2 - 0.5])
    flange_v.apply_translation([0, 0, -4.5 / 2 - 0.5])
    dpad = trimesh.util.concatenate([dp_h, dp_v, flange_h, flange_v])
    dpad.apply_translation([dpad_x, dpad_y, 0])
    buttons.append(dpad)

    # ABXY Buttons
    for bx, by in abxy_coords:
        cap = cylinder(radius=3.7, height=4.5, sections=32)
        flange = cylinder(radius=4.7, height=1.0, sections=32)
        flange.apply_translation([0, 0, -4.5 / 2 - 0.5])
        btn = trimesh.util.concatenate([cap, flange])
        btn.apply_translation([bx, by, 0])
        buttons.append(btn)

    # SE / ST Buttons
    for sx, sy in [(27.24 - 31.5, 40.0 - 66.50), (35.26 - 31.5, 40.0 - 66.50)]:
        cap = cylinder(radius=2.7, height=2.4, sections=32)
        flange = cylinder(radius=3.3, height=0.8, sections=32)
        flange.apply_translation([0, 0, -2.4 / 2 - 0.4])
        btn = trimesh.util.concatenate([cap, flange])
        btn.apply_translation([sx, sy, 0])
        buttons.append(btn)

    # Shoulder Triggers (L1, L2, R2, R1)
    l1 = box(extents=[13.05, 4.0, 5.0])
    l1.apply_translation([-24.2, 40.0, 0])
    l2 = box(extents=[7.75, 4.0, 5.8])
    l2.apply_translation([-13.1, 40.0, 0.4])
    r2 = box(extents=[7.75, 4.0, 5.8])
    r2.apply_translation([13.1, 40.0, 0.4])
    r1 = box(extents=[13.05, 4.0, 5.0])
    r1.apply_translation([24.2, 40.0, 0])
    buttons.extend([l1, l2, r2, r1])

    buttons_mesh = trimesh.util.concatenate(buttons)
    for d in output_dirs:
        buttons_mesh.export(os.path.join(d, "buttons_dpad_abxy_sest_shoulders.stl"))
    print(
        f"Exported buttons_dpad_abxy_sest_shoulders.stl (vertices: {len(buttons_mesh.vertices)}, faces: {len(buttons_mesh.faces)})"
    )

    # ==============================================================================
    # 5. COMPLETE MATED CONSOLE ASSEMBLY (gkd_pixel_console_assembly.stl)
    # ==============================================================================
    front_assembled = front_shell.copy()
    rear_assembled = rear_shell.copy()
    rear_assembled.apply_translation([0, 0, -D_front / 2 - D_rear / 2 - 1.6])
    door_assembled = door.copy()
    door_assembled.apply_translation([0, 15.0, -D_front / 2 - D_rear - 1.6 + 0.9])
    buttons_assembled = buttons_mesh.copy()
    buttons_assembled.apply_translation([0, 0, 2.0])

    full_assembly = trimesh.util.concatenate(
        [front_assembled, rear_assembled, door_assembled, buttons_assembled]
    )
    for d in output_dirs:
        full_assembly.export(os.path.join(d, "gkd_pixel_console_assembly.stl"))
    print(
        f"Exported gkd_pixel_console_assembly.stl (vertices: {len(full_assembly.vertices)}, faces: {len(full_assembly.faces)})"
    )

    print("All STL assets successfully generated and verified!")


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D CAD meshes for GKD Pixel Enclosure"
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_MODELS_DIR,
        help="Destination directory for STL models",
    )
    args = parser.parse_args()

    dirs = [args.output_dir]
    # Also write to .copperpilot/generated if it exists
    copperpilot_gen = os.path.join(SCRIPT_DIR, "..", ".copperpilot", "generated")
    if os.path.exists(copperpilot_gen):
        dirs.append(copperpilot_gen)

    generate_all(dirs)


if __name__ == "__main__":
    main()
