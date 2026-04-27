"""Render a quick PNG preview of an OBJ in Blender.

Run from the repo root:

blender --background --python blender/scripts/render_obj_preview.py -- outputs/obj/form.obj outputs/previews/form.png
"""

import sys
from pathlib import Path

import bpy


def parse_args():
    if "--" not in sys.argv:
        raise SystemExit("Expected args after --: input.obj output.png")
    args = sys.argv[sys.argv.index("--") + 1 :]
    if len(args) != 2:
        raise SystemExit("Usage: blender --background --python render_obj_preview.py -- input.obj output.png")
    return Path(args[0]), Path(args[1])


def main():
    obj_path, png_path = parse_args()
    png_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    bpy.ops.wm.obj_import(filepath=str(obj_path))
    imported = bpy.context.selected_objects
    if not imported:
        raise SystemExit(f"No objects imported from {obj_path}")

    obj = imported[0]
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # Center object.
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    obj.location = (0, 0, 0)

    # Add camera and light.
    bpy.ops.object.light_add(type="AREA", location=(2.8, -4.0, 5.0))
    light = bpy.context.object
    light.data.energy = 450
    light.data.size = 5

    bpy.ops.object.camera_add(location=(3.0, -5.5, 3.2), rotation=(1.1, 0, 0.50))
    bpy.context.scene.camera = bpy.context.object

    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 900
    bpy.context.scene.render.filepath = str(png_path)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
