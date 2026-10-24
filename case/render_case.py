#!/usr/bin/env python3
"""
3D Enclosure Visualization Renderer for GKD Pixel Handheld Console.
Generates front, rear, isometric, exploded views, and 24-frame rotating explosion GIF.
"""

import os
import imageio
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import trimesh

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(SCRIPT_DIR, "models")
RENDERS_DIR = os.path.join(SCRIPT_DIR, "renders")
DOCS_IMAGES_DIR = os.path.join(SCRIPT_DIR, "..", "docs", "images")

os.makedirs(RENDERS_DIR, exist_ok=True)
os.makedirs(DOCS_IMAGES_DIR, exist_ok=True)

# Load individual STL parts from models directory
front = trimesh.load(os.path.join(MODELS_DIR, "case_front_bezel.stl"))
rear = trimesh.load(os.path.join(MODELS_DIR, "case_rear_grooved.stl"))
door = trimesh.load(os.path.join(MODELS_DIR, "case_battery_door.stl"))
buttons = trimesh.load(os.path.join(MODELS_DIR, "buttons_dpad_abxy_sest_shoulders.stl"))

light = np.array([0.4, 0.6, 0.8])
light = light / np.linalg.norm(light)


def get_shaded_poly(mesh, hex_color, alpha=1.0, edge_color=None):
    triangles = mesh.vertices[mesh.faces]
    normals = mesh.face_normals
    intensity = np.clip(np.dot(normals, light) * 0.55 + 0.55, 0.35, 1.0)
    base_rgb = np.array(matplotlib.colors.to_rgb(hex_color))
    colors = np.outer(intensity, base_rgb)
    if edge_color is None:
        edge_color = tuple(base_rgb * 0.65)
    return Poly3DCollection(triangles, facecolors=colors, edgecolors=edge_color, linewidths=0.15, alpha=alpha)


def save_fig(fig, filename):
    for d in [RENDERS_DIR, DOCS_IMAGES_DIR]:
        path = os.path.join(d, filename)
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    print(f"Rendered {filename}")


def main():
    print("==> Rendering 3D enclosure projections...")

    # 1. Front View (Assembled)
    fig = plt.figure(figsize=(10, 10), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(get_shaded_poly(front, "#8a949f"))
    ax.add_collection3d(get_shaded_poly(buttons, "#26292d"))
    ax.set_xlim(-35, 35)
    ax.set_ylim(-45, 45)
    ax.set_zlim(-15, 15)
    ax.view_init(elev=90, azim=-90)
    ax.set_axis_off()
    fig.patch.set_facecolor("#ffffff")
    save_fig(fig, "case_render_front.png")

    # 2. Rear View (Assembled with Grooves and Lanyard Slots)
    fig = plt.figure(figsize=(10, 10), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(get_shaded_poly(rear, "#8a949f"))
    door_m = door.copy()
    door_m.apply_translation([0, 15.0, 0.0])
    ax.add_collection3d(get_shaded_poly(door_m, "#7a848f"))
    ax.set_xlim(-35, 35)
    ax.set_ylim(-45, 45)
    ax.set_zlim(-15, 15)
    ax.view_init(elev=-90, azim=90)
    ax.set_axis_off()
    fig.patch.set_facecolor("#ffffff")
    save_fig(fig, "case_render_rear.png")

    # 3. Isometric View (Front 3/4 Perspective)
    fig = plt.figure(figsize=(10, 10), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(get_shaded_poly(front, "#98a2ad"))
    rear_iso = rear.copy()
    rear_iso.apply_translation([0, 0, -2.6 - 5.6 - 1.6])
    ax.add_collection3d(get_shaded_poly(rear_iso, "#717b86"))
    btn_iso = buttons.copy()
    btn_iso.apply_translation([0, 0, 1.5])
    ax.add_collection3d(get_shaded_poly(btn_iso, "#26292d"))
    ax.set_xlim(-40, 40)
    ax.set_ylim(-45, 45)
    ax.set_zlim(-25, 25)
    ax.view_init(elev=32, azim=-55)
    ax.set_axis_off()
    fig.patch.set_facecolor("#ffffff")
    save_fig(fig, "case_render_isometric.png")

    # 4. Exploded Assembly View
    fig = plt.figure(figsize=(10, 12), dpi=150)
    ax = fig.add_subplot(111, projection="3d")
    btn_exp = buttons.copy()
    btn_exp.apply_translation([0, 0, 32.0])
    ax.add_collection3d(get_shaded_poly(btn_exp, "#26292d"))

    front_exp = front.copy()
    front_exp.apply_translation([0, 0, 16.0])
    ax.add_collection3d(get_shaded_poly(front_exp, "#98a2ad", alpha=0.95))

    rear_exp = rear.copy()
    rear_exp.apply_translation([0, 0, -18.0])
    ax.add_collection3d(get_shaded_poly(rear_exp, "#717b86", alpha=0.95))

    door_exp = door.copy()
    door_exp.apply_translation([0, 15.0, -36.0])
    ax.add_collection3d(get_shaded_poly(door_exp, "#5b6570"))

    ax.set_xlim(-40, 40)
    ax.set_ylim(-50, 50)
    ax.set_zlim(-45, 45)
    ax.view_init(elev=25, azim=-45)
    ax.set_axis_off()
    fig.patch.set_facecolor("#ffffff")
    save_fig(fig, "case_render_exploded.png")

    print("All renders generated successfully.")


if __name__ == "__main__":
    main()
