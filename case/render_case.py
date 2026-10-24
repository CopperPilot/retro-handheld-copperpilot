#!/usr/bin/env python3
"""
High-Resolution 3D Enclosure & PCBA Assembly Visualization Suite for GKD Pixel Console.
Generates smooth, anti-aliased engineering renders, exploded views, side-by-side reference
comparisons, and a step-by-step 3D assembly motion animation (GIF and MP4 video).
"""

import os
import subprocess
import imageio
import numpy as np
from PIL import Image
import pyvista as pv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
RENDERS_DIR = os.path.join(SCRIPT_DIR, "renders")
DOCS_IMAGES_DIR = os.path.join(ROOT_DIR, "docs", "images")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

os.makedirs(RENDERS_DIR, exist_ok=True)
os.makedirs(DOCS_IMAGES_DIR, exist_ok=True)


def build_scene_assets():
    """Loads and prepares all CAD meshes with feature-angle normal smoothing and proper materials."""
    front = pv.read(os.path.join(MODELS_DIR, "case_front_bezel.stl")).compute_normals(
        feature_angle=30.0, split_vertices=True
    )
    rear = pv.read(os.path.join(MODELS_DIR, "case_rear_grooved.stl")).compute_normals(
        feature_angle=30.0, split_vertices=True
    )
    door = pv.read(os.path.join(MODELS_DIR, "case_battery_door.stl")).compute_normals(
        feature_angle=30.0, split_vertices=True
    )
    buttons = pv.read(os.path.join(MODELS_DIR, "buttons_dpad_abxy_sest_shoulders.stl")).compute_normals(
        feature_angle=30.0, split_vertices=True
    )

    # 2.4" Display Panel Module: Glass face + PCB backing frame
    display_glass = pv.Box(bounds=[-25.0, 25.0, 14.07 - 19.0, 14.07 + 19.0, 1.8, 2.6])
    display_pcb = pv.Box(bounds=[-27.5, 27.5, 14.07 - 21.5, 14.07 + 21.5, 0.4, 1.8])

    # 4-Layer FR-4 PCB (63.0 x 80.0 x 1.6 mm) with corner mounting holes and snap notches
    pcb = pv.Box(bounds=[-31.5, 31.5, -40.0, 40.0, -1.6, 0.0])

    # Populated PCBA Components:
    # Front tactile switches under D-pad and ABXY
    sw_front = []
    # D-pad switches
    for sx, sy in [(-16.85, -20.96 + 6.3), (-16.85, -20.96 - 6.3), (-16.85 - 6.3, -20.96), (-16.85 + 6.3, -20.96)]:
        sw = pv.Box(bounds=[sx - 3.0, sx + 3.0, sy - 3.0, sy + 3.0, 0.0, 2.5])
        sw_front.append(sw)
    # ABXY switches
    for bx, by in [(16.51, -15.42), (9.92, -21.74), (23.05, -21.83), (16.39, -28.02)]:
        sw = pv.Box(bounds=[bx - 3.0, bx + 3.0, by - 3.0, by + 3.0, 0.0, 2.5])
        sw_front.append(sw)
    # Display connector J3
    j3 = pv.Box(bounds=[31.5 - 7.5 - 31.5, 31.5 + 7.5 - 31.5, 40.0 - 46.0 - 2.5, 40.0 - 46.0 + 2.5, 0.0, 1.65])
    sw_front.append(j3)

    pcba_front_parts = sw_front[0]
    for s in sw_front[1:]:
        pcba_front_parts = pcba_front_parts.merge(s)

    # Back components: ESP32-S3 module, USB-C, JST-PH, Power ICs
    esp32 = pv.Box(bounds=[-9.0, 9.0, 40.0 - 16.0 - 12.75, 40.0 - 16.0 + 12.75, -4.75, -1.6])
    usbc = pv.Box(bounds=[-4.5, 4.5, -40.0, -40.0 + 7.5, -4.8, -1.6])
    jst_ph = pv.Box(bounds=[15.0 - 31.5 - 3.0, 15.0 - 31.5 + 3.0, 40.0 - 39.0 - 3.8, 40.0 - 39.0 + 3.8, -7.6, -1.6])
    pcba_back_parts = esp32.merge(usbc).merge(jst_ph)

    # 1000 mAh Li-Po Cell (40.0 x 30.0 x 8.0 mm)
    battery = pv.Box(bounds=[-20.0, 20.0, 15.0 - 15.0, 15.0 + 15.0, -9.6, -1.6])

    return {
        "front": front,
        "rear": rear,
        "door": door,
        "buttons": buttons,
        "display_glass": display_glass,
        "display_pcb": display_pcb,
        "pcb": pcb,
        "pcba_front": pcba_front_parts,
        "pcba_back": pcba_back_parts,
        "battery": battery,
    }


def setup_lighting(plotter):
    """Configures multi-point studio key, fill, and rim lighting for high-end rendering."""
    key = pv.Light(position=(85, 80, 120), focal_point=(0, 0, 0), color="white", intensity=0.90)
    fill = pv.Light(position=(-85, -30, 80), focal_point=(0, 0, 0), color="#d8e2ec", intensity=0.45)
    rim = pv.Light(position=(0, 100, -80), focal_point=(0, 0, 0), color="#ffffff", intensity=0.35)
    plotter.add_light(key)
    plotter.add_light(fill)
    plotter.add_light(rim)


def save_render(plotter, filename):
    for d in [RENDERS_DIR, DOCS_IMAGES_DIR]:
        path = os.path.join(d, filename)
        plotter.screenshot(path)
    print(f"    Saved {filename}")


def render_front_view(assets):
    print("==> [1/6] Rendering High-Resolution Front View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1600])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    front = assets["front"].copy()
    glass = assets["display_glass"].copy()
    buttons = assets["buttons"].copy()
    buttons.translate([0, 0, 1.8])

    p.add_mesh(front, color="#747c87", smooth_shading=True, specular=0.4, specular_power=25)
    p.add_mesh(glass, color="#090a0d", smooth_shading=True, specular=0.85, specular_power=80)
    p.add_mesh(buttons, color="#22252a", smooth_shading=True, specular=0.3, specular_power=20)

    p.camera_position = [(0, 0, 160), (0, 0, 0), (0, 1, 0)]
    p.reset_camera()
    p.camera.zoom(0.92)
    save_render(p, "case_render_front.png")
    p.close()


def render_rear_view(assets):
    print("==> [2/6] Rendering High-Resolution Rear Grooved Shell View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1600])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    rear = assets["rear"].copy()
    door = assets["door"].copy()
    door.translate([0, 15.0, -5.6 + 0.9])

    p.add_mesh(rear, color="#747c87", smooth_shading=True, specular=0.4, specular_power=25)
    p.add_mesh(door, color="#585e68", smooth_shading=True, specular=0.4, specular_power=25)

    p.camera_position = [(0, 0, -160), (0, 0, 0), (0, 1, 0)]
    p.reset_camera()
    p.camera.zoom(0.92)
    save_render(p, "case_render_rear.png")
    p.close()


def render_isometric_view(assets):
    print("==> [3/6] Rendering 3/4 Isometric Perspective View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1600])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    front = assets["front"].copy()
    rear = assets["rear"].copy()
    door = assets["door"].copy()
    buttons = assets["buttons"].copy()
    glass = assets["display_glass"].copy()

    buttons.translate([0, 0, 1.8])
    rear.translate([0, 0, -2.6 - 5.6])
    door.translate([0, 15.0, -2.6 - 11.2 + 0.9])

    p.add_mesh(front, color="#79818c", smooth_shading=True, specular=0.45, specular_power=30)
    p.add_mesh(rear, color="#5d636e", smooth_shading=True, specular=0.45, specular_power=30)
    p.add_mesh(door, color="#4e535c", smooth_shading=True, specular=0.45, specular_power=30)
    p.add_mesh(glass, color="#08090b", smooth_shading=True, specular=0.90, specular_power=90)
    p.add_mesh(buttons, color="#25282e", smooth_shading=True, specular=0.35, specular_power=20)

    p.camera_position = [(85, 45, 125), (0, 0, -3), (0, 1, 0)]
    p.reset_camera()
    p.camera.zoom(0.92)
    save_render(p, "case_render_isometric.png")
    p.close()


def render_exploded_view(assets):
    print("==> [4/6] Rendering Exploded Subsystem Assembly View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1800])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    # Explode components along Z axis
    buttons = assets["buttons"].copy()
    buttons.translate([0, 0, 48.0])

    front = assets["front"].copy()
    front.translate([0, 0, 24.0])

    disp_glass = assets["display_glass"].copy()
    disp_glass.translate([0, 0, 14.0])
    disp_pcb = assets["display_pcb"].copy()
    disp_pcb.translate([0, 0, 13.0])

    pcb = assets["pcb"].copy()
    pcba_f = assets["pcba_front"].copy()
    pcba_b = assets["pcba_back"].copy()

    rear = assets["rear"].copy()
    rear.translate([0, 0, -26.0])

    battery = assets["battery"].copy()
    battery.translate([0, 0, -42.0])

    door = assets["door"].copy()
    door.translate([0, 15.0, -56.0])

    p.add_mesh(buttons, color="#25282e", smooth_shading=True, specular=0.3)
    p.add_mesh(front, color="#79818c", smooth_shading=True, opacity=0.92, specular=0.4)
    p.add_mesh(disp_glass, color="#090a0d", smooth_shading=True, specular=0.8)
    p.add_mesh(disp_pcb, color="#1e3a5f", smooth_shading=True)
    p.add_mesh(pcb, color="#1b4d3e", smooth_shading=True, specular=0.2)  # High-grade Green/Black FR-4
    p.add_mesh(pcba_f, color="#c0a060", smooth_shading=True, specular=0.5)  # Gold/tactile switches
    p.add_mesh(pcba_b, color="#2b2e35", smooth_shading=True, specular=0.5)  # Shield cans & ICs
    p.add_mesh(rear, color="#5d636e", smooth_shading=True, opacity=0.92, specular=0.4)
    p.add_mesh(battery, color="#206095", smooth_shading=True, specular=0.3)  # Blue Li-Po cell
    p.add_mesh(door, color="#4e535c", smooth_shading=True, specular=0.4)

    p.camera_position = [(95, 60, 140), (0, 0, -5), (0, 1, 0)]
    p.reset_camera()
    p.camera.zoom(0.92)
    save_render(p, "case_render_exploded.png")
    p.close()


def generate_reference_comparisons():
    print("==> [5/6] Generating Side-by-Side Reference Comparisons...")
    comparisons = [
        ("comparison_front.png", "Screenshot 2026-10-23 at 5.48.16 PM.png", "case_render_front.png", "Target Hardware Reference", "3D CAD Enclosure Model"),
        ("comparison_rear.png", "Screenshot 2026-10-23 at 5.48.12 PM.png", "case_render_rear.png", "Target Hardware Reference", "3D CAD Enclosure Model"),
        ("comparison_isometric.png", "Screenshot 2026-10-23 at 5.48.22 PM.png", "case_render_isometric.png", "Target Industrial Design", "3D CAD Enclosure Model"),
    ]

    for out_name, ref_name, render_name, label_ref, label_cad in comparisons:
        ref_path = os.path.join(ASSETS_DIR, ref_name)
        render_path = os.path.join(DOCS_IMAGES_DIR, render_name)
        if not os.path.exists(ref_path) or not os.path.exists(render_path):
            continue

        im_ref = Image.open(ref_path).convert("RGBA")
        im_cad = Image.open(render_path).convert("RGBA")

        # Normalize both to height 1000px preserving aspect ratio
        target_h = 1000
        w_ref = int(im_ref.width * (target_h / im_ref.height))
        w_cad = int(im_cad.width * (target_h / im_cad.height))
        im_ref = im_ref.resize((w_ref, target_h), Image.Resampling.LANCZOS)
        im_cad = im_cad.resize((w_cad, target_h), Image.Resampling.LANCZOS)

        # Composite side by side with clean divider
        total_w = w_ref + w_cad + 20
        combined = Image.new("RGBA", (total_w, target_h), (251, 252, 253, 255))
        combined.paste(im_ref, (0, 0))
        combined.paste(im_cad, (w_ref + 20, 0))

        for d in [RENDERS_DIR, DOCS_IMAGES_DIR]:
            combined.save(os.path.join(d, out_name), quality=95)
        print(f"    Saved side-by-side comparison {out_name}")


def generate_assembly_motion_animation(assets):
    print("==> [6/6] Generating 3D Sequential Assembly Motion Animation (GIF & MP4)...")
    p = pv.Plotter(off_screen=True, window_size=[720, 720])
    p.set_background("#f8f9fa")
    setup_lighting(p)

    total_frames = 64
    frames = []

    # Nominal assembled Z positions:
    # Front Bezel: Z = +2.6
    # Buttons: seated in front bezel
    # Display: seated in front shelf
    # PCBA: seated against alignment bosses (Z = 0)
    # Rear Shell: snapped behind PCBA (Z = -8.2)
    # Battery: seated in rear bay (Z = -5.6)
    # Battery Door: snapped shut (Z = -11.2)

    p.camera_position = [(80, 50, 115), (0, 0, -4), (0, 1, 0)]
    p.reset_camera()
    p.camera.zoom(0.92)

    for frame_idx in range(total_frames):
        p.clear()
        setup_lighting(p)

        t = frame_idx / (total_frames - 1)  # 0.0 to 1.0

        # Phase 1 (0.0 to 0.20): PCBA components populate onto bare PCB
        pcb_z = 0.0
        p_pcb = assets["pcb"].copy()
        p.add_mesh(p_pcb, color="#1b4d3e", smooth_shading=True)

        if t >= 0.08:
            sw_offset = max(0.0, 15.0 * (1.0 - (t - 0.08) / 0.10)) if t < 0.18 else 0.0
            p_sw = assets["pcba_front"].copy()
            p_sw.translate([0, 0, sw_offset])
            p.add_mesh(p_sw, color="#c0a060", smooth_shading=True)

            back_offset = max(0.0, -15.0 * (1.0 - (t - 0.08) / 0.10)) if t < 0.18 else 0.0
            p_back = assets["pcba_back"].copy()
            p_back.translate([0, 0, back_offset])
            p.add_mesh(p_back, color="#2b2e35", smooth_shading=True)

        # Phase 2 (0.20 to 0.40): Front Bezel & Buttons slide in
        if t >= 0.20:
            front_offset = max(0.0, 45.0 * (1.0 - (t - 0.20) / 0.15)) if t < 0.35 else 0.0
            p_front = assets["front"].copy()
            p_front.translate([0, 0, 2.6 + front_offset])
            p.add_mesh(p_front, color="#79818c", smooth_shading=True, opacity=0.95)

            p_btn = assets["buttons"].copy()
            btn_offset = max(0.0, 60.0 * (1.0 - (t - 0.20) / 0.15)) if t < 0.35 else 0.0
            p_btn.translate([0, 0, 4.4 + btn_offset])
            p.add_mesh(p_btn, color="#25282e", smooth_shading=True)

        # Phase 3 (0.35 to 0.55): 2.4" Display Panel seats into front bezel
        if t >= 0.35:
            disp_offset = max(0.0, 30.0 * (1.0 - (t - 0.35) / 0.15)) if t < 0.50 else 0.0
            p_glass = assets["display_glass"].copy()
            p_glass.translate([0, 0, disp_offset])
            p.add_mesh(p_glass, color="#08090b", smooth_shading=True, specular=0.85)

        # Phase 4 (0.50 to 0.70): Rear Grooved Shell closes and snaps shut
        if t >= 0.50:
            rear_offset = max(0.0, -45.0 * (1.0 - (t - 0.50) / 0.15)) if t < 0.65 else 0.0
            p_rear = assets["rear"].copy()
            p_rear.translate([0, 0, -8.2 - rear_offset])
            p.add_mesh(p_rear, color="#5d636e", smooth_shading=True, opacity=0.95)

        # Phase 5 (0.65 to 0.82): Battery inserts into rear bay
        if t >= 0.65:
            bat_offset = max(0.0, -35.0 * (1.0 - (t - 0.65) / 0.12)) if t < 0.77 else 0.0
            p_bat = assets["battery"].copy()
            p_bat.translate([0, 0, -4.8 - bat_offset])
            p.add_mesh(p_bat, color="#206095", smooth_shading=True)

        # Phase 6 (0.75 to 0.90): Battery door snaps shut
        if t >= 0.75:
            door_offset = max(0.0, -30.0 * (1.0 - (t - 0.75) / 0.12)) if t < 0.87 else 0.0
            p_door = assets["door"].copy()
            p_door.translate([0, 15.0, -11.9 - door_offset])
            p.add_mesh(p_door, color="#4e535c", smooth_shading=True)

        # Phase 7 (0.87 to 1.0): Gentle 3D turntable rotation showing completed console
        if t >= 0.87:
            p.camera.Azimuth(2.5 * (frame_idx - total_frames * 0.87))

        img = p.screenshot(return_img=True)
        frames.append(img)

    p.close()

    # Save animated GIF (12 FPS)
    gif_path = os.path.join(DOCS_IMAGES_DIR, "case_explosion_animation.gif")
    imageio.mimsave(gif_path, frames, duration=1000 // 12, loop=0)
    # Also save to renders
    imageio.mimsave(os.path.join(RENDERS_DIR, "case_explosion_animation.gif"), frames, duration=1000 // 12, loop=0)
    print(f"    Saved assembly animation GIF: {gif_path} ({len(frames)} frames)")

    # Save MP4 video via ffmpeg if available
    mp4_path = os.path.join(DOCS_IMAGES_DIR, "case_assembly_video.mp4")
    try:
        writer = imageio.get_writer(mp4_path, fps=15, codec="libx264", quality=8)
        for f in frames:
            writer.append_data(f)
        writer.close()
        print(f"    Saved assembly MP4 video: {mp4_path}")
    except Exception as e:
        print(f"    Video encoding fallback: {e}")


def main():
    print("======================================================================")
    print("GKD Pixel Console: High-Resolution 3D Visualization Pipeline")
    print("======================================================================")
    assets = build_scene_assets()
    render_front_view(assets)
    render_rear_view(assets)
    render_isometric_view(assets)
    render_exploded_view(assets)
    generate_reference_comparisons()
    generate_assembly_motion_animation(assets)
    print("======================================================================")
    print("ALL VISUAL ASSETS GENERATED SUCCESSFULLY!")
    print("======================================================================")


if __name__ == "__main__":
    main()
