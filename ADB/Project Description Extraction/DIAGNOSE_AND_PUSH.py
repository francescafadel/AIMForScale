#!/usr/bin/env python3
"""
Diagnose why Project Description Extraction isn't showing on GitHub, then copy and show git status.

Run from the folder that contains the ADB folder (e.g. "ADB Project Description Extraction"):
  python3 DIAGNOSE_AND_PUSH.py
  python3 DIAGNOSE_AND_PUSH.py /path/to/AIMForScale

If run from inside ADB/Project Description Extraction/, uses parent/ADB.
"""

import shutil
import subprocess
import sys
from pathlib import Path

THIS_DIR = Path(__file__).parent.resolve()
# If we're inside repo at ADB/Project Description Extraction/, parent is ADB
if THIS_DIR.parent.name == "ADB" and (THIS_DIR.parent / "Project Description Extraction").exists():
    LOCAL_ADB = THIS_DIR.parent
else:
    LOCAL_ADB = THIS_DIR / "ADB"
PDE = LOCAL_ADB / "Project Description Extraction"
DEFAULT_AIM = Path.home() / "Desktop" / "AIMForScale"


def main():
    aim_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_AIM

    print("=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    print(f"This script is in:     {THIS_DIR}")
    print(f"Local ADB folder:      {LOCAL_ADB}")
    print(f"  exists?              {LOCAL_ADB.is_dir()}")
    print(f"Project Description Extraction: {PDE}")
    print(f"  exists?              {PDE.is_dir()}")
    if PDE.is_dir():
        kids = list(PDE.iterdir())
        print(f"  contents (top-level): {[p.name for p in kids]}")
    print(f"AIMForScale path:      {aim_path}")
    print(f"  exists?              {aim_path.is_dir()}")
    if aim_path.is_dir():
        aim_adb = aim_path / "ADB"
        aim_pde = aim_adb / "Project Description Extraction"
        print(f"  ADB exists?          {aim_adb.is_dir()}")
        print(f"  ADB/Project Description Extraction exists? {aim_pde.is_dir()}")
    print("=" * 60)

    if not LOCAL_ADB.is_dir():
        print("ERROR: ADB folder missing.")
        sys.exit(1)
    if not PDE.is_dir():
        print("ERROR: Project Description Extraction folder missing inside ADB.")
        sys.exit(1)
    if not aim_path.is_dir():
        print("ERROR: AIMForScale folder not found. Clone it or run: python3 DIAGNOSE_AND_PUSH.py /path/to/AIMForScale")
        sys.exit(1)

    aim_adb = aim_path / "ADB"
    aim_adb.mkdir(parents=True, exist_ok=True)
    for name in ["README.md", "CONTENTS.md"]:
        src = LOCAL_ADB / name
        if src.is_file():
            shutil.copy2(src, aim_adb / name)
            print(f"Copied {name} -> ADB/")
    (aim_adb / "ADB Links").mkdir(parents=True, exist_ok=True)
    if (LOCAL_ADB / "ADB Links" / "README.md").is_file():
        shutil.copy2(LOCAL_ADB / "ADB Links" / "README.md", aim_adb / "ADB Links" / "README.md")
    pde_dst = aim_adb / "Project Description Extraction"
    if pde_dst.exists():
        shutil.rmtree(pde_dst)
    shutil.copytree(PDE, pde_dst)
    print("Copied full Project Description Extraction/ -> ADB/")

    print("\n" + "=" * 60)
    print("GIT STATUS (inside AIMForScale)")
    print("=" * 60)
    try:
        r = subprocess.run(
            ["git", "status", "--short", "ADB/"],
            cwd=aim_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
        out = (r.stdout or "").strip() or "(no output)"
        print(out)
    except Exception as e:
        print("Could not run git:", e)
    print("=" * 60)
    print("\nNow run: cd", aim_path, "&& git add ADB/ && git commit -m 'Add ADB' && git push origin main")
    print("=" * 60)


if __name__ == "__main__":
    main()
