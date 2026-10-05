"""Procedurally builds the FBX sources in fbx/. Run: blender -b -P make_fbx.py"""
import math
import os

import bmesh
import bpy

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fbx")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def material(name):
    return bpy.data.materials.new(name)


def new_object(name, bm, materials=()):
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    for mat in materials:
        mesh.materials.append(mat)
    mesh.polygons.foreach_set("use_smooth", [False] * len(mesh.polygons))
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def add_second_uv_and_colors(bm):
    uv0 = bm.loops.layers.uv.verify()
    uv1 = bm.loops.layers.uv.new("UVChannel_1")
    colors = bm.loops.layers.color.new("VertexColors")
    for face in bm.faces:
        for loop in face.loops:
            u, v = loop[uv0].uv
            loop[uv1].uv = (v, 1 - u)
            loop[colors] = (abs(loop.vert.co.x) / 50 % 1, abs(loop.vert.co.y) / 50 % 1, abs(loop.vert.co.z) / 50 % 1, 1)


def cube_object(name, size=100):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=size, calc_uvs=True)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0, 0, size / 2))
    add_second_uv_and_colors(bm)
    for index, face in enumerate(bm.faces):
        face.material_index = index % 2
    return new_object(name, bm, [material("MaterialA"), material("MaterialB")])


def sphere_object(name, segments, rings, radius=50):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, calc_uvs=True)
    add_second_uv_and_colors(bm)
    return new_object(name, bm, [material("Material")])


def plane_object(name, size=400, cells=8):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=cells, y_segments=cells, size=size / 2, calc_uvs=True)
    add_second_uv_and_colors(bm)
    return new_object(name, bm, [material("Material")])


def tower_object(name, segments=4, segment_height=50, half=20):
    bm = bmesh.new()
    for segment in range(segments):
        created = bmesh.ops.create_cube(bm, size=1.0, calc_uvs=True)
        bmesh.ops.scale(bm, verts=created["verts"], vec=(half * 2, half * 2, segment_height))
        bmesh.ops.translate(bm, verts=created["verts"], vec=(0, 0, segment_height * (segment + 0.5)))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    add_second_uv_and_colors(bm)
    return new_object(name, bm, [material("Material")])


def skin_to_bones(obj, bone_heights):
    """Weights each vertex between the two bones whose heights bracket it."""
    for name in bone_heights:
        obj.vertex_groups.new(name=name)
    names = list(bone_heights)
    for vertex in obj.data.vertices:
        height = vertex.co.z
        for index, name in enumerate(names):
            lower = bone_heights[names[index - 1]] if index else None
            upper = bone_heights[names[index + 1]] if index + 1 < len(names) else None
            center = bone_heights[name]
            if height <= center:
                weight = 1.0 if lower is None else max(0.0, 1 - (center - height) / (center - lower))
            else:
                weight = 1.0 if upper is None else max(0.0, 1 - (height - center) / (upper - center))
            if weight > 0:
                obj.vertex_groups[name].add([vertex.index], weight, "REPLACE")


def skeletal_object(name):
    tower = tower_object(name)
    bone_heights = {"root": 0, "middle": 100, "tip": 200}
    armature_data = bpy.data.armatures.new(f"{name}_Armature")
    armature = bpy.data.objects.new("Armature", armature_data)
    bpy.context.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    parent = None
    for bone_name, height in bone_heights.items():
        bone = armature_data.edit_bones.new(bone_name)
        bone.head = (0, 0, height)
        bone.tail = (0, 0, height + 100)
        bone.parent = parent
        bone.use_connect = parent is not None
        parent = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    skin_to_bones(tower, bone_heights)
    tower.parent = armature
    tower.modifiers.new("Armature", "ARMATURE").object = armature

    bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, 31
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="POSE")
    for bone_name, degrees in (("middle", 40), ("tip", -30)):
        pose_bone = armature.pose.bones[bone_name]
        pose_bone.rotation_mode = "XYZ"
        for frame, angle in ((1, 0), (16, degrees), (31, 0)):
            pose_bone.rotation_euler = (0, math.radians(angle), 0)
            pose_bone.keyframe_insert("rotation_euler", frame=frame)
    bpy.ops.object.mode_set(mode="OBJECT")
    armature.animation_data.action.name = "A_Bend"
    return armature, tower


def export(name, objects, animation=False):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUTPUT, f"{name}.fbx"), use_selection=True, object_types={"MESH", "ARMATURE"},
                             add_leaf_bones=False, bake_anim=animation, mesh_smooth_type="FACE", use_mesh_modifiers=True,
                             axis_forward="-Z", axis_up="Y", apply_unit_scale=True, global_scale=1.0, apply_scale_options="FBX_SCALE_NONE")


os.makedirs(OUTPUT, exist_ok=True)
for name, build in (("SM_Cube", lambda n: cube_object(n)), ("SM_Sphere", lambda n: sphere_object(n, 24, 16)), ("SM_Plane", lambda n: plane_object(n)),
                    ("SM_DenseSphere", lambda n: sphere_object(n, 96, 64)), ("SM_Lods", lambda n: sphere_object(n, 48, 32))):
    reset_scene()
    export(name, [build(name)])
reset_scene()
armature, tower = skeletal_object("SK_Tower")
export("SK_Tower", [armature, tower], animation=True)
