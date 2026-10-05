import os

import unreal

ROOT = "/Game/Lib"
FBX_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fbx")

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
editor_assets = unreal.EditorAssetLibrary
editor_level = unreal.EditorLevelLibrary


def create_asset(folder, name, asset_class, factory):
    asset = asset_tools.create_asset(name, f"{ROOT}/{folder}", asset_class, factory)
    if asset is None:
        raise RuntimeError(f"could not create {folder}/{name}")
    return asset


def import_file(path, folder, name, options=None):
    task = unreal.AssetImportTask()
    task.filename = path
    task.destination_path = f"{ROOT}/{folder}"
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.options = options
    asset_tools.import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError(f"importing {path} produced nothing")
    return [unreal.load_asset(object_path) for object_path in task.imported_object_paths]


def fbx_options(skeletal):
    options = unreal.FbxImportUI()
    mesh_type = unreal.FBXImportType.FBXIT_SKELETAL_MESH if skeletal else unreal.FBXImportType.FBXIT_STATIC_MESH
    options.set_editor_properties({"import_mesh": True, "import_as_skeletal": skeletal, "import_animations": skeletal, "create_physics_asset": skeletal,
                                   "import_materials": False, "import_textures": False, "automated_import_should_detect_type": False,
                                   "mesh_type_to_import": mesh_type})
    return options


def import_asset(path, folder, name, asset_class, options):
    imported = import_file(path, folder, name, options)
    unreal.log("imported %s: %s" % (name, [type(asset).__name__ for asset in imported]))
    return next(asset for asset in imported if isinstance(asset, asset_class))


def find_asset(folder, asset_class):
    for path in editor_assets.list_assets(f"{ROOT}/{folder}"):
        asset = unreal.load_asset(path)
        if isinstance(asset, asset_class):
            return asset
    raise RuntimeError(f"no {asset_class.__name__} in {folder}")


def load(folder, name):
    return unreal.load_asset(f"{ROOT}/{folder}/{name}")


def duplicate_engine_asset(source, folder, name):
    return editor_assets.duplicate_asset(source, f"{ROOT}/{folder}/{name}")


def engine_major_minor():
    major, minor = unreal.SystemLibrary.get_engine_version().split("-")[0].split(".")[:2]
    return int(major), int(minor)
