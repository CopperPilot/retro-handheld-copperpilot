#!/usr/bin/env python3
"""
High-Resolution 3D Enclosure & PCBA Assembly Visualization Suite for GKD Pixel Console.
Generates smooth, anti-aliased engineering renders, exploded views, side-by-side reference
comparisons, and a realistic step-by-step 3D assembly motion animation (GIF and MP4 video)
using genuine 3D exports from KiCad (GLB/STL) and parametric CAD models.
"""

import os
import subprocess
import imageio
import numpy as np
from PIL import Image
import pyvista as pv
import trimesh

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
RENDERS_DIR = os.path.join(SCRIPT_DIR, "renders")
DOCS_IMAGES_DIR = os.path.join(ROOT_DIR, "docs", "images")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

os.makedirs(RENDERS_DIR, exist_ok=True)
os.makedirs(DOCS_IMAGES_DIR, exist_ok=True)


def build_scene_assets():
    """Loads all CAD meshes with feature-angle normal smoothing, including genuine KiCad 3D PCBA."""
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

    # 1. Genuine KiCad 3D PCBA with full realistic colors & materials
    glb_path = os.path.join(MODELS_DIR, "gameboy_pcb_populated.glb")
    if not os.path.exists(glb_path):
        # Generate on the fly using kicad-cli if missing
        pcb_file = os.path.join(ROOT_DIR, "gameboy-copperpilot.kicad_pcb")
        subprocess.run(["kicad-cli", "pcb", "export", "glb", "--output", glb_path, "--force", pcb_file], check=True)

    scene = trimesh.load(glb_path)
    mesh = scene.to_geometry()
    mesh.apply_scale(1000.0)  # Convert meters to mm

    # Transform from KiCad GLTF to Case Coordinate Frame:
    # KiCad X: [0, 63] -> Case X: [-31.5, +31.5]
    # KiCad Z (thickness): [-4.9, 5.9] -> Case Z
    # KiCad Y: [0, 80] (top to bottom) -> Case Y: [+40, -40]
    verts = mesh.vertices.copy()
    x_case = verts[:, 0] - 31.5
    y_case = 40.0 - verts[:, 2]
    z_case = verts[:, 1]
    case_verts = np.column_stack([x_case, y_case, z_case])

    faces = np.pad(mesh.faces, ((0, 0), (1, 0)), constant_values=3).ravel()
    pcb_full = pv.PolyData(case_verts, faces)
    vertex_colors = mesh.visual.to_color().vertex_colors[:, :3]
    pcb_full.point_data["RGB"] = vertex_colors

    # Also build a bare PCB substrate mesh (for Stage 1 animation)
    bare_pcb = pv.Box(bounds=[-31.5, 31.5, -40.0, 40.0, -1.6, 0.0])

    # 2. 2.4" Display Panel Module (Waveshare 15933 / ER-TFT024-3, ILI9341 SPI TFT):
    # Glass face (54.0 x 42.0 x 1.6 mm) + PCB backing frame (55.0 x 43.0 x 1.2 mm) + FPC ribbon
    display_glass = pv.Box(bounds=[-27.0, 27.0, 14.07 - 21.0, 14.07 + 21.0, 1.8, 3.4])
    display_pcb = pv.Box(bounds=[-27.5, 27.5, 14.07 - 21.5, 14.07 + 21.5, 0.6, 1.8])
    display_ribbon = pv.Box(bounds=[-4.0, 4.0, -8.0, 14.07 - 21.5, 0.2, 1.0])

    # 3. 1000 mAh Li-Po Battery Pack (LP803040 / 40.0 x 30.0 x 7.5 mm) with JST-PH leads
    battery = pv.Box(bounds=[-15.0, 15.0, -26.0, 14.0, -10.3, -2.8])

    return {
        "front": front,
        "rear": rear,
        "door": door,
        "buttons": buttons,
        "pcb_full": pcb_full,
        "bare_pcb": bare_pcb,
        "display_glass": display_glass,
        "display_pcb": display_pcb,
        "display_ribbon": display_ribbon,
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

    p.add_mesh(front, color="#747c87", smooth_shading=True, specular=0.4, specular_power=25)
    p.add_mesh(glass, color="#090a0d", smooth_shading=True, specular=0.85, specular_power=80)
    p.add_mesh(buttons, color="#22252a", smooth_shading=True, specular=0.3, specular_power=20)

    p.reset_camera()
    p.camera_position = [(0, 0, 160), (0, 0, 0), (0, 1, 0)]
    p.camera.zoom(0.92)
    save_render(p, "case_render_front.png")
    p.close()


def render_rear_view(assets):
    print("==> [2/6] Rendering High-Resolution Rear Grooved Shell View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1600])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    rear = assets["rear"].copy()

    p.add_mesh(rear, color="#747c87", smooth_shading=True, specular=0.4, specular_power=25)

    p.reset_camera()
    p.camera_position = [(0, 0, -160), (0, 0, 0), (0, 1, 0)]
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
    buttons = assets["buttons"].copy()
    glass = assets["display_glass"].copy()

    p.add_mesh(front, color="#79818c", smooth_shading=True, specular=0.45, specular_power=30)
    p.add_mesh(rear, color="#5d636e", smooth_shading=True, specular=0.45, specular_power=30)
    p.add_mesh(glass, color="#08090b", smooth_shading=True, specular=0.90, specular_power=90)
    p.add_mesh(buttons, color="#25282e", smooth_shading=True, specular=0.35, specular_power=20)

    p.reset_camera()
    p.camera_position = [(85, 45, 125), (0, 0, -3), (0, 1, 0)]
    p.camera.zoom(0.92)
    save_render(p, "case_render_isometric.png")
    p.close()


def render_exploded_view(assets):
    print("==> [4/6] Rendering Exploded Subsystem Assembly View with KiCad 3D PCBA...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1200])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    # Explode components cleanly along Z axis
    buttons = assets["buttons"].copy()
    buttons.translate([0, 0, 80.0], inplace=True)

    front = assets["front"].copy()
    front.translate([0, 0, 48.0], inplace=True)

    disp_glass = assets["display_glass"].copy()
    disp_glass.translate([0, 0, 26.0], inplace=True)
    disp_pcb = assets["display_pcb"].copy()
    disp_pcb.translate([0, 0, 25.0], inplace=True)
    disp_ribbon = assets["display_ribbon"].copy()
    disp_ribbon.translate([0, 0, 16.0], inplace=True)

    # Genuine KiCad 3D Populated PCBA centered at Z = 0
    pcb_full = assets["pcb_full"].copy()

    battery = assets["battery"].copy()
    battery.translate([0, 0, -25.0], inplace=True)

    rear = assets["rear"].copy()
    rear.translate([0, 0, -55.0], inplace=True)

    p.add_mesh(buttons, color="#25282e", smooth_shading=True, specular=0.3)
    p.add_mesh(front, color="#79818c", smooth_shading=True, opacity=0.92, specular=0.4)
    p.add_mesh(disp_glass, color="#090a0d", smooth_shading=True, specular=0.8)
    p.add_mesh(disp_pcb, color="#1e3a5f", smooth_shading=True)
    p.add_mesh(disp_ribbon, color="#c0a060", smooth_shading=True)
    p.add_mesh(pcb_full, rgb=True, smooth_shading=True, specular=0.3)
    p.add_mesh(battery, color="#206095", smooth_shading=True, specular=0.3)
    p.add_mesh(rear, color="#5d636e", smooth_shading=True, opacity=0.92, specular=0.4)

    # Side 3/4 perspective looking across the Z explode axis
    p.camera.position = (180.0, 40.0, 70.0)
    p.camera.focal_point = (0.0, 0.0, 10.0)
    p.camera.up = (0.0, 1.0, 0.0)
    p.camera.zoom(1.1)
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

    total_frames = 80
    frames = []

    cam_pos = (135.0, 65.0, 140.0)
    cam_focal = (0.0, 0.0, 0.0)
    cam_up = (0.0, 1.0, 0.0)
    rad = np.hypot(cam_pos[0], cam_pos[2])
    init_theta = np.arctan2(cam_pos[0], cam_pos[2])

    for frame_idx in range(total_frames):
        p.clear()
        setup_lighting(p)

        t = frame_idx / (total_frames - 1)  # 0.0 to 1.0

        # Maintain smooth, stable camera framing
        if t < 0.82:
            p.camera.position = cam_pos
            p.camera.focal_point = cam_focal
            p.camera.up = cam_up
        else:
            # Stage 6: 360-degree turntable orbit of fully assembled console
            orbit_frac = (t - 0.82) / 0.18
            angle = orbit_frac * 2.0 * np.pi
            th = init_theta + angle
            cur_x = rad * np.sin(th)
            cur_z = rad * np.cos(th)
            p.camera.position = (cur_x, cam_pos[1], cur_z)
            p.camera.focal_point = cam_focal
            p.camera.up = cam_up

        # ======================================================================
        # STAGE 1 (t: 0.0 to 0.18): Bare PCB -> PCBA Component Populating
        # ======================================================================
        if t < 0.18:
            blend = t / 0.18
            p_pcb = assets["bare_pcb"].copy()
            p.add_mesh(p_pcb, color="#1b4d3e", smooth_shading=True)
            comp_offset = (1.0 - blend) * 30.0
            p_full = assets["pcb_full"].copy()
            p_full.translate([0, 0, comp_offset], inplace=True)
            p.add_mesh(p_full, rgb=True, smooth_shading=True, opacity=max(0.1, blend))
        else:
            p_full = assets["pcb_full"].copy()
            p.add_mesh(p_full, rgb=True, smooth_shading=True)

        # ======================================================================
        # STAGE 2 (t: 0.18 to 0.38): Front Bezel & Gamepad Buttons Enter
        # ======================================================================
        if t >= 0.18:
            front_blend = min(1.0, (t - 0.18) / 0.14)
            front_offset = (1.0 - front_blend) * 55.0
            p_front = assets["front"].copy()
            p_front.translate([0, 0, front_offset], inplace=True)
            p.add_mesh(p_front, color="#79818c", smooth_shading=True, opacity=0.95)

            # Buttons slide into front bezel bores from above
            btn_blend = min(1.0, max(0.0, (t - 0.22) / 0.14))
            btn_offset = (1.0 - btn_blend) * 75.0
            p_btn = assets["buttons"].copy()
            p_btn.translate([0, 0, btn_offset], inplace=True)
            p.add_mesh(p_btn, color="#25282e", smooth_shading=True)

        # ======================================================================
        # STAGE 3 (t: 0.36 to 0.55): 2.4" Display Panel seats & connects to J3
        # ======================================================================
        if t >= 0.36:
            disp_blend = min(1.0, (t - 0.36) / 0.14)
            disp_offset = (1.0 - disp_blend) * 40.0
            p_glass = assets["display_glass"].copy()
            p_glass.translate([0, 0, disp_offset], inplace=True)
            p.add_mesh(p_glass, color="#08090b", smooth_shading=True, specular=0.85)

            p_disp_pcb = assets["display_pcb"].copy()
            p_disp_pcb.translate([0, 0, disp_offset], inplace=True)
            p.add_mesh(p_disp_pcb, color="#1e3a5f", smooth_shading=True)

            p_ribbon = assets["display_ribbon"].copy()
            p_ribbon.translate([0, 0, disp_offset], inplace=True)
            p.add_mesh(p_ribbon, color="#c0a060", smooth_shading=True)

        # ======================================================================
        # STAGE 4 (t: 0.54 to 0.72): 1000 mAh Li-Po Battery Inserts into Cavity
        # ======================================================================
        if t >= 0.54:
            bat_blend = min(1.0, (t - 0.54) / 0.14)
            bat_offset = (1.0 - bat_blend) * -45.0
            p_bat = assets["battery"].copy()
            p_bat.translate([0, 0, bat_offset], inplace=True)
            p.add_mesh(p_bat, color="#206095", smooth_shading=True)

        # ======================================================================
        # STAGE 5 (t: 0.70 to 0.84): Rear Grooved Shell closes & snaps flush
        # ======================================================================
        if t >= 0.70:
            rear_blend = min(1.0, (t - 0.70) / 0.12)
            rear_offset = (1.0 - rear_blend) * -55.0
            p_rear = assets["rear"].copy()
            p_rear.translate([0, 0, rear_offset], inplace=True)
            p.add_mesh(p_rear, color="#5d636e", smooth_shading=True, opacity=0.95)

        img = p.screenshot(return_img=True)
        frames.append(img)

    p.close()

    # Save animated GIF (15 FPS)
    gif_path = os.path.join(DOCS_IMAGES_DIR, "case_explosion_animation.gif")
    imageio.mimsave(gif_path, frames, duration=1000 // 15, loop=0)
    imageio.mimsave(os.path.join(RENDERS_DIR, "case_explosion_animation.gif"), frames, duration=1000 // 15, loop=0)
    print(f"    Saved assembly animation GIF: {gif_path} ({len(frames)} frames)")

    # Save MP4 video via ffmpeg / imageio (15 FPS)
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
