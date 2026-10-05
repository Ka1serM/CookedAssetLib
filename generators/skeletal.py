import os

import unreal

from common import FBX_DIR, create_asset, fbx_options, import_asset, load


def generate():
    path = os.path.join(FBX_DIR, "SK_Tower.fbx")
    mesh = import_asset(path, "SkeletalMesh", "SK_Tower", unreal.SkeletalMesh, fbx_options(skeletal=True))
    slot = mesh.get_editor_property("materials")[0]
    slot.set_editor_property("material_interface", load("Material", "M_VertexColor"))
    mesh.set_editor_property("materials", [slot])
    skeleton = mesh.get_editor_property("skeleton")

    for name, asset_class, factory in (("BS_Bend", unreal.BlendSpace1D, unreal.BlendSpaceFactory1D()),
                                       ("ABP_Tower", unreal.AnimBlueprint, unreal.AnimBlueprintFactory())):
        if not hasattr(factory, "target_skeleton"):
            unreal.log_warning(f"{name} skipped: {type(factory).__name__} does not expose target_skeleton in this engine version")
            continue
        factory.set_editor_property("target_skeleton", skeleton)
        create_asset("SkeletalMesh", name, asset_class, factory)
