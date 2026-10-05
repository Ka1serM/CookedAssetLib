"""Builds the source asset set in /Game/Lib. Runs inside the editor of UE 4.26+ (Python scripting)."""
import os
import struct
import tempfile
import zlib

import unreal

ROOT = "/Game/Lib"
TEXTURE_SIZE = 256

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_editing = unreal.MaterialEditingLibrary
editor_assets = unreal.EditorAssetLibrary
editor_level = unreal.EditorLevelLibrary


def png_chunk(kind, data):
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def write_checker_png(path):
    rows = bytearray()
    for y in range(TEXTURE_SIZE):
        rows.append(0)
        for x in range(TEXTURE_SIZE):
            blue = 255 if (x // 32 + y // 32) % 2 else 64
            rows += bytes((x, y, blue, 255))
    header = struct.pack(">IIBBBBB", TEXTURE_SIZE, TEXTURE_SIZE, 8, 6, 0, 0, 0)
    with open(path, "wb") as file:
        file.write(b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header)
                   + png_chunk(b"IDAT", zlib.compress(bytes(rows))) + png_chunk(b"IEND", b""))


def import_texture(png, name, virtual):
    task = unreal.AssetImportTask()
    task.filename = png
    task.destination_path = f"{ROOT}/Texture"
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    asset_tools.import_asset_tasks([task])
    texture = unreal.load_asset(f"{ROOT}/Texture/{name}")
    texture.set_editor_property("virtual_texture_streaming", virtual)
    return texture


def create_textured_material(name, texture):
    material = asset_tools.create_asset(name, f"{ROOT}/Material", unreal.Material, unreal.MaterialFactoryNew())
    sample = material_editing.create_material_expression(material, unreal.MaterialExpressionTextureSample, -400, 0)
    sample.set_editor_property("texture", texture)
    material_editing.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    material_editing.recompile_material(material)
    return material


def duplicate_engine_asset(source, destination):
    return editor_assets.duplicate_asset(source, f"{ROOT}/{destination}")


png_path = os.path.join(tempfile.gettempdir(), "checker.png")
write_checker_png(png_path)

texture = import_texture(png_path, "T_Checker", virtual=False)
virtual_texture = import_texture(png_path, "T_CheckerVirtual", virtual=True)
material = create_textured_material("M_Checker", texture)
virtual_material = create_textured_material("M_CheckerVirtual", virtual_texture)

cube = duplicate_engine_asset("/Engine/BasicShapes/Cube", "StaticMesh/SM_Cube")
sphere = duplicate_engine_asset("/Engine/BasicShapes/Sphere", "StaticMesh/SM_Sphere")
cube.set_material(0, material)
sphere.set_material(0, virtual_material)
skeletal_cube = duplicate_engine_asset("/Engine/EngineMeshes/SkeletalCube", "SkeletalMesh/SK_Cube")

editor_level.new_level(f"{ROOT}/Map/TestMap")
editor_level.spawn_actor_from_object(cube, unreal.Vector(0, 0, 50))
editor_level.spawn_actor_from_object(sphere, unreal.Vector(300, 0, 50))
editor_level.spawn_actor_from_object(skeletal_cube, unreal.Vector(-300, 0, 50))
editor_level.save_current_level()

editor_assets.save_directory(ROOT)
unreal.log("generate_assets: done")
