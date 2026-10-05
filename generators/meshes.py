import os

import unreal

from common import FBX_DIR, engine_major_minor, fbx_options, import_asset, load


def import_static_mesh(name, materials):
    static_mesh = import_asset(os.path.join(FBX_DIR, f"{name}.fbx"), "StaticMesh", name, unreal.StaticMesh, fbx_options(skeletal=False))
    for slot, material_name in enumerate(materials):
        static_mesh.set_material(slot, load("Material", material_name))
    return static_mesh


def generate():
    cube = import_static_mesh("SM_Cube", ["M_Checker", "M_Opaque"])
    unreal.EditorStaticMeshLibrary.add_simple_collisions(cube, unreal.ScriptingCollisionShapeType.BOX)
    sphere = import_static_mesh("SM_Sphere", ["M_CheckerVirtual"])
    unreal.EditorStaticMeshLibrary.add_simple_collisions(sphere, unreal.ScriptingCollisionShapeType.SPHERE)
    import_static_mesh("SM_Plane", ["M_Tiled"])
    dense = import_static_mesh("SM_DenseSphere", ["M_Opaque"])
    if engine_major_minor() >= (5, 0):
        dense.set_editor_property("nanite_settings", unreal.MeshNaniteSettings(enabled=True))
    lods = unreal.EditorScriptingMeshReductionOptions(auto_compute_lod_screen_size=False, reduction_settings=[
        unreal.EditorScriptingMeshReductionSettings(percent_triangles=1.0, screen_size=1.0),
        unreal.EditorScriptingMeshReductionSettings(percent_triangles=0.25, screen_size=0.4)])
    unreal.EditorStaticMeshLibrary.set_lods(import_static_mesh("SM_Lods", ["M_Opaque"]), lods)
