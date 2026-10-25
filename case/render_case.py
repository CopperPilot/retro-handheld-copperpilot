#!/usr/bin/env python3
"""
High-Resolution 3D Enclosure & PCBA Assembly Visualization Suite for the CopperPilot Retro Handheld.
Generates smooth, anti-aliased engineering renders, exploded views, and a realistic step-by-step 3D assembly motion animation (GIF and MP4 video)
using genuine 3D exports from KiCad (GLB/STL) and parametric CAD models.
"""

import os
import subprocess

import imageio
import numpy as np
import pyvista as pv
import trimesh

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
RENDERS_DIR = os.path.join(SCRIPT_DIR, "renders")
DOCS_IMAGES_DIR = os.path.join(ROOT_DIR, "docs", "images")

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
    buttons = pv.read(
        os.path.join(MODELS_DIR, "buttons_dpad_abxy_sest_shoulders.stl")
    ).compute_normals(feature_angle=30.0, split_vertices=True)

    # 1. Genuine KiCad 3D PCBA with full realistic colors & materials
    glb_path = os.path.join(MODELS_DIR, "copperpilot_retro_handheld_pcb_populated.glb")
    if not os.path.exists(glb_path):
        # Generate on the fly using kicad-cli if missing
        pcb_file = os.path.join(ROOT_DIR, "copperpilot-retro-handheld.kicad_pcb")
        subprocess.run(
            [
                "kicad-cli",
                "pcb",
                "export",
                "glb",
                "--output",
                glb_path,
                "--force",
                pcb_file,
            ],
            check=True,
        )

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
    # Active display area: 48.96 x 36.72 mm
    # Display glass sits inside internal shelf at Z in [4.30, 5.30] mm
    # Display PCB sits at Z in [3.45, 4.25] mm (clearing J2 through-hole pins at Z <= 3.32 mm)
    # FPC ribbon connects to J3 from Y = -2.0 to -6.0 mm at Z = 5.86 mm
    display_glass = pv.Box(bounds=[-24.5, 24.5, 14.5 - 17.5, 14.5 + 17.5, 4.30, 5.30])
    display_pcb = pv.Box(bounds=[-25.0, 25.0, 14.5 - 16.5, 14.5 + 16.5, 3.45, 4.25])
    display_ribbon = pv.Box(bounds=[-4.0, 4.0, -6.0, -1.8, 5.76, 5.96])

    # 3. 1000 mAh Li-Po Battery Pack (26.0 x 38.0 x 6.0 mm) placed in rear cavity
    battery = pv.Box(
        bounds=[3.0 - 13.0, 3.0 + 13.0, -8.0 - 19.0, -8.0 + 19.0, -9.0, -3.0]
    )

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
    key = pv.Light(
        position=(85, 80, 120), focal_point=(0, 0, 0), color="white", intensity=0.90
    )
    fill = pv.Light(
        position=(-85, -30, 80), focal_point=(0, 0, 0), color="#d8e2ec", intensity=0.45
    )
    rim = pv.Light(
        position=(0, 100, -80), focal_point=(0, 0, 0), color="#ffffff", intensity=0.35
    )
    plotter.add_light(key)
    plotter.add_light(fill)
    plotter.add_light(rim)


def save_render(plotter, filename):
    for d in [RENDERS_DIR, DOCS_IMAGES_DIR]:
        path = os.path.join(d, filename)
        plotter.screenshot(path)
    print(f"    Saved {filename}")


def render_front_view(assets):
    print("==> [1/5] Rendering High-Resolution Front View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1600])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    front = assets["front"].copy()
    glass = assets["display_glass"].copy()
    buttons = assets["buttons"].copy()

    p.add_mesh(
        front, color="#747c87", smooth_shading=True, specular=0.4, specular_power=25
    )
    p.add_mesh(
        glass, color="#090a0d", smooth_shading=True, specular=0.85, specular_power=80
    )
    p.add_mesh(
        buttons, color="#22252a", smooth_shading=True, specular=0.3, specular_power=20
    )

    p.reset_camera()
    p.camera_position = [(0, 0, 160), (0, 0, 0), (0, 1, 0)]
    p.camera.zoom(0.92)
    save_render(p, "case_render_front.png")
    p.close()


def render_rear_view(assets):
    print("==> [2/5] Rendering High-Resolution Rear Grooved Shell View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1600])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    rear = assets["rear"].copy()

    p.add_mesh(
        rear, color="#747c87", smooth_shading=True, specular=0.4, specular_power=25
    )

    p.reset_camera()
    p.camera_position = [(0, 0, -160), (0, 0, 0), (0, 1, 0)]
    p.camera.zoom(0.92)
    save_render(p, "case_render_rear.png")
    p.close()


def render_isometric_view(assets):
    print("==> [3/5] Rendering 3/4 Isometric Perspective View...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1600])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    front = assets["front"].copy()
    rear = assets["rear"].copy()
    buttons = assets["buttons"].copy()
    glass = assets["display_glass"].copy()

    p.add_mesh(
        front, color="#79818c", smooth_shading=True, specular=0.45, specular_power=30
    )
    p.add_mesh(
        rear, color="#5d636e", smooth_shading=True, specular=0.45, specular_power=30
    )
    p.add_mesh(
        glass, color="#08090b", smooth_shading=True, specular=0.90, specular_power=90
    )
    p.add_mesh(
        buttons, color="#25282e", smooth_shading=True, specular=0.35, specular_power=20
    )

    p.reset_camera()
    p.camera_position = [(85, 45, 125), (0, 0, -3), (0, 1, 0)]
    p.camera.zoom(0.92)
    save_render(p, "case_render_isometric.png")
    p.close()


def render_exploded_view(assets):
    print("==> [4/5] Rendering Exploded Subsystem Assembly View with KiCad 3D PCBA...")
    p = pv.Plotter(off_screen=True, window_size=[1600, 1200])
    p.set_background("#fbfcfd")
    setup_lighting(p)

    # Explode components cleanly along Z axis
    buttons = assets["buttons"].copy()
    buttons.translate([0, 0, 68.0], inplace=True)

    front = assets["front"].copy()
    front.translate([0, 0, 44.0], inplace=True)

    disp_glass = assets["display_glass"].copy()
    disp_glass.translate([0, 0, 22.0], inplace=True)
    disp_pcb = assets["display_pcb"].copy()
    disp_pcb.translate([0, 0, 21.0], inplace=True)
    disp_ribbon = assets["display_ribbon"].copy()
    disp_ribbon.translate([0, 0, 14.0], inplace=True)

    # Genuine KiCad 3D Populated PCBA centered at Z = 0
    pcb_full = assets["pcb_full"].copy()

    battery = assets["battery"].copy()
    battery.translate([0, 0, -22.0], inplace=True)

    rear = assets["rear"].copy()
    rear.translate([0, 0, -48.0], inplace=True)

    p.add_mesh(buttons, color="#25282e", smooth_shading=True, specular=0.3)
    p.add_mesh(front, color="#79818c", smooth_shading=True, opacity=0.92, specular=0.4)
    p.add_mesh(disp_glass, color="#090a0d", smooth_shading=True, specular=0.8)
    p.add_mesh(disp_pcb, color="#1e3a5f", smooth_shading=True)
    p.add_mesh(disp_ribbon, color="#c0a060", smooth_shading=True)
    p.add_mesh(pcb_full, rgb=True, smooth_shading=True, specular=0.3)
    p.add_mesh(battery, color="#206095", smooth_shading=True, specular=0.3)
    p.add_mesh(rear, color="#5d636e", smooth_shading=True, opacity=0.92, specular=0.4)

    # Side 3/4 perspective looking across the Z explode axis
    p.camera.position = (185.0, 45.0, 65.0)
    p.camera.focal_point = (0.0, 0.0, 10.0)
    p.camera.up = (0.0, 1.0, 0.0)
    p.camera.zoom(0.85)
    save_render(p, "case_render_exploded.png")
    p.close()


def generate_assembly_motion_animation(assets):
    print("==> [5/5] Generating 3D Sequential Assembly Motion Animation (GIF & MP4)...")
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

        # Maintain smooth, stable camera framing during assembly stages
        if t < 0.86:
            p.camera.position = cam_pos
            p.camera.focal_point = cam_focal
            p.camera.up = cam_up
        else:
            # Stage 7: 360-degree turntable orbit of fully assembled console
            orbit_frac = (t - 0.86) / 0.14
            angle = orbit_frac * 2.0 * np.pi
            th = init_theta + angle
            cur_x = rad * np.sin(th)
            cur_z = rad * np.cos(th)
            p.camera.position = (cur_x, cam_pos[1], cur_z)
            p.camera.focal_point = cam_focal
            p.camera.up = cam_up

        # ======================================================================
        # STAGE 1 (t: 0.0 to 0.16): Bare PCB -> PCBA Component Populating
        # ======================================================================
        if t < 0.16:
            blend = t / 0.16
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
        # STAGE 2 (t: 0.16 to 0.32): Gamepad Buttons seat onto PCBA Switches
        # Buttons fly down along +Z and seat directly onto tactile switch actuators
        # ======================================================================
        if t >= 0.16:
            btn_blend = min(1.0, (t - 0.16) / 0.14)
            btn_offset = (1.0 - btn_blend) * 65.0
            p_btn = assets["buttons"].copy()
            p_btn.translate([0, 0, btn_offset], inplace=True)
            p.add_mesh(p_btn, color="#25282e", smooth_shading=True)

        # ======================================================================
        # STAGE 3 (t: 0.32 to 0.48): 2.4" Display Panel seats & connects to J3
        # Display descends along +Z and connects FPC ribbon cleanly into JST-GH J3
        # ======================================================================
        if t >= 0.32:
            disp_blend = min(1.0, (t - 0.32) / 0.14)
            disp_offset = (1.0 - disp_blend) * 60.0
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
        # STAGE 4 (t: 0.48 to 0.64): Front Bezel lowers over Buttons & Display
        # Front bezel lowers along +Z; bores slide over button caps and frame screen
        # ======================================================================
        if t >= 0.48:
            front_blend = min(1.0, (t - 0.48) / 0.14)
            front_offset = (1.0 - front_blend) * 60.0
            p_front = assets["front"].copy()
            p_front.translate([0, 0, front_offset], inplace=True)
            p.add_mesh(p_front, color="#79818c", smooth_shading=True, opacity=0.95)

        # ======================================================================
        # STAGE 5 (t: 0.64 to 0.76): 1000 mAh Li-Po Battery Inserts into Cavity
        # Battery seats into lower rear cavity and mates with JST-PH connector J2
        # ======================================================================
        if t >= 0.64:
            bat_blend = min(1.0, (t - 0.64) / 0.10)
            bat_offset = (1.0 - bat_blend) * -50.0
            p_bat = assets["battery"].copy()
            p_bat.translate([0, 0, bat_offset], inplace=True)
            p.add_mesh(p_bat, color="#206095", smooth_shading=True)

        # ======================================================================
        # STAGE 6 (t: 0.76 to 0.86): Rear Grooved Shell closes & snaps flush
        # Rear shell moves along -Z, engaging pins H1-H4 and snapping flush
        # ======================================================================
        if t >= 0.76:
            rear_blend = min(1.0, (t - 0.76) / 0.10)
            rear_offset = (1.0 - rear_blend) * -60.0
            p_rear = assets["rear"].copy()
            p_rear.translate([0, 0, rear_offset], inplace=True)
            p.add_mesh(p_rear, color="#5d636e", smooth_shading=True, opacity=0.95)

        img = p.screenshot(return_img=True)
        frames.append(img)

    p.close()

    # Save animated GIF (15 FPS)
    gif_path = os.path.join(DOCS_IMAGES_DIR, "case_explosion_animation.gif")
    imageio.mimsave(gif_path, frames, duration=1000 // 15, loop=0)
    imageio.mimsave(
        os.path.join(RENDERS_DIR, "case_explosion_animation.gif"),
        frames,
        duration=1000 // 15,
        loop=0,
    )
    print(f"    Saved assembly animation GIF: {gif_path} ({len(frames)} frames)")

    # Save MP4 video via ffmpeg / imageio (15 FPS)
    mp4_path = os.path.join(DOCS_IMAGES_DIR, "case_assembly_video.mp4")
    try:
        writer = imageio.get_writer(mp4_path, fps=15, codec="libx264", quality=8)
        for f in frames:
            writer.append_data(f)
        writer.close()
        print(f"    Saved assembly MP4 video: {mp4_path}")
    except Exception as e:  # noqa: BLE001 - MP4 export is best-effort; the GIF is already saved
        print(f"    Video encoding fallback: {e}")


def main():
    print("======================================================================")
    print("CopperPilot Retro Handheld: High-Resolution 3D Visualization Pipeline")
    print("======================================================================")
    assets = build_scene_assets()
    render_front_view(assets)
    render_rear_view(assets)
    render_isometric_view(assets)
    render_exploded_view(assets)
    generate_assembly_motion_animation(assets)
    print("======================================================================")
    print("ALL VISUAL ASSETS GENERATED SUCCESSFULLY!")
    print("======================================================================")


if __name__ == "__main__":
    main()
