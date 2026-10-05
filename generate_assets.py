"""Builds the source asset set in /Game/Lib and writes Saved/generation.json. Runs inside the editor of UE 4.26+ (Python scripting)."""
import importlib
import json
import os
import sys
import traceback

import unreal

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "generators"))

GENERATORS = ["textures", "materials", "meshes", "skeletal", "audio", "data", "blueprints", "maps"]

results = {}
for name in GENERATORS:
    try:
        importlib.import_module(name).generate()
        results[name] = "ok"
    except Exception:
        results[name] = traceback.format_exc()
        unreal.log_error(f"generator {name} failed:\n{results[name]}")
    unreal.EditorAssetLibrary.save_directory("/Game/Lib")

with open(os.path.join(unreal.Paths.project_saved_dir(), "generation.json"), "w") as file:
    json.dump({"engine": unreal.SystemLibrary.get_engine_version(), "generators": results}, file, indent=2)
