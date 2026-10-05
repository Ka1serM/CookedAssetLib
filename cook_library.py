"""Generates the source asset set and cooks it with each requested UE version.

Usage: python cook_library.py 4.26 5.8 ...
Layout: <LIBRARY_ROOT>/projects/<version> holds the generated project, <LIBRARY_ROOT>/library/<version> the paks and generation.json.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

LIBRARY_ROOT = Path("E:/UELibrary")
ENGINE_ROOTS = [Path("C:/Program Files/Epic Games"), Path("C:/Epic Games")]
GENERATOR = Path(__file__).resolve().with_name("generate_assets.py")
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


def run(command, check=True):
    print(">", " ".join(str(part) for part in command), flush=True)
    subprocess.run([str(part) for part in command], check=check)


def generate(engine, uproject):
    # Some engine versions crash while the editor shuts down; generation.json is the verdict, not the exit code.
    run([editor_cmd(engine), uproject, f"-ExecutePythonScript={GENERATOR}", "-unattended", "-nosplash", "-nullrhi", "-stdout", "-FullStdOutLogOutput"], check=False)


def read_generation_report(project_dir):
    report_path = project_dir / "Saved/generation.json"
    if not report_path.exists():
        sys.exit("the editor exited without writing generation.json")
    report = json.loads(report_path.read_text())
    failed = {name: error for name, error in report["generators"].items() if error != "ok"}
    for name, error in failed.items():
        print(f"generator {name} failed:\n{error}")
    if failed:
        sys.exit(f"generators failed: {', '.join(failed)}")


def cook(engine, uproject, project_dir, output_dir):
    run([engine / "Engine/Build/BatchFiles/RunUAT.bat", "BuildCookRun", f"-project={uproject}", "-noP4", "-platform=Win64",
         "-clientconfig=Development", "-build", "-cook", "-stage", "-pak", "-unattended"])
    (paks,) = project_dir.glob(f"Saved/StagedBuilds/*/{PROJECT_NAME}/Content/Paks")
    shutil.rmtree(output_dir, ignore_errors=True)
    shutil.copytree(paks, output_dir / "Paks")
    shutil.copy(project_dir / "Saved/generation.json", output_dir)


def main(versions):
    for version in versions:
        engine = find_engine(version)
        project_dir = LIBRARY_ROOT / "projects" / version
        uproject = write_project(project_dir, version)
        generate(engine, uproject)
        read_generation_report(project_dir)
        cook(engine, uproject, project_dir, LIBRARY_ROOT / "library" / version)


if __name__ == "__main__":
    main(sys.argv[1:])
