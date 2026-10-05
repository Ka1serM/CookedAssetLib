"""Generates the source asset set and cooks it with each requested UE version.

Usage: python cook_library.py 4.26 5.8 ...
Layout: <LIBRARY_ROOT>/projects/<version> holds the generated project, <LIBRARY_ROOT>/library/<version> the cooked result.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

LIBRARY_ROOT = Path("E:/UELibrary")
ENGINE_ROOTS = [Path("C:/Program Files/Epic Games"), Path("C:/Epic Games")]
GENERATOR = Path(__file__).with_name("generate_assets.py")
PROJECT_NAME = "CookedLib"

DEFAULT_ENGINE_INI = """[/Script/Engine.RendererSettings]
r.VirtualTextures=True
"""


def find_engine(version):
    for root in ENGINE_ROOTS:
        engine = root / f"UE_{version}"
        if (engine / "Engine/Build/BatchFiles/RunUAT.bat").exists():
            return engine
    sys.exit(f"UE {version} is not installed")


def editor_cmd(engine):
    binaries = engine / "Engine/Binaries/Win64"
    for name in ("UnrealEditor-Cmd.exe", "UE4Editor-Cmd.exe"):
        if (binaries / name).exists():
            return binaries / name
    sys.exit(f"no editor in {binaries}")


def write_project(project_dir, version):
    shutil.rmtree(project_dir, ignore_errors=True)
    (project_dir / "Config").mkdir(parents=True)
    (project_dir / "Config/DefaultEngine.ini").write_text(DEFAULT_ENGINE_INI)
    uproject = {
        "FileVersion": 3,
        "EngineAssociation": version,
        "Category": "",
        "Description": "",
        "Plugins": [{"Name": "PythonScriptPlugin", "Enabled": True},
                    {"Name": "EditorScriptingUtilities", "Enabled": True}],
    }
    path = project_dir / f"{PROJECT_NAME}.uproject"
    path.write_text(json.dumps(uproject, indent=2))
    return path


def run(command):
    print(">", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], check=True)


def generate(engine, uproject):
    run([editor_cmd(engine), uproject, f"-ExecutePythonScript={GENERATOR}", "-unattended", "-nosplash", "-nullrhi", "-stdout", "-FullStdOutLogOutput"])


def cook(engine, uproject, output_dir):
    shutil.rmtree(output_dir, ignore_errors=True)
    run([engine / "Engine/Build/BatchFiles/RunUAT.bat", "BuildCookRun", f"-project={uproject}", "-noP4", "-platform=Win64",
         "-clientconfig=Development", "-cook", "-stage", "-pak", "-archive", f"-archivedirectory={output_dir}", "-unattended"])


def main(versions):
    for version in versions:
        engine = find_engine(version)
        project_dir = LIBRARY_ROOT / "projects" / version
        uproject = write_project(project_dir, version)
        generate(engine, uproject)
        cook(engine, uproject, LIBRARY_ROOT / "library" / version)


if __name__ == "__main__":
    main(sys.argv[1:])
