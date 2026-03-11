"""
Copy the full ADB folder (including Project Description Extraction) into your
AIMForScale repo so you can push it to GitHub.

Run this from the same folder as this script, then run the git commands it prints.

Usage:
  1. Clone AIMForScale if you haven't: git clone https://github.com/francescafadel/AIMForScale.git
  2. Set AIMForScale path below (or pass as argument).
  3. Run: python push_adb_to_github.py
  4. Run the git commands it prints (cd to AIMForScale, add, commit, push).

Note: When this file lives in the repo at ADB/Project Description Extraction/,
run it from the parent folder that contains the ADB folder (e.g. "ADB Project Description Extraction").
"""

import shutil
import sys
from pathlib import Path

# When run from "ADB Project Description Extraction" folder, parent is script's parent's parent
THIS_DIR = Path(__file__).parent.resolve()
# If we're inside Project Description Extraction, LOCAL_ADB is sibling ADB folder (parent / "ADB")
if (THIS_DIR.parent / "ADB").is_dir():
    LOCAL_ADB = THIS_DIR.parent / "ADB"
else:
    LOCAL_ADB = THIS_DIR / "ADB"

DEFAULT_AIMFORSCALE = Path.home() / "Desktop" / "AIMForScale"


def main():
    if len(sys.argv) > 1:
        aim_path = Path(sys.argv[1]).resolve()
    else:
        aim_path = DEFAULT_AIMFORSCALE

    if not LOCAL_ADB.is_dir():
        print(f"ERROR: ADB folder not found at {LOCAL_ADB}")
        sys.exit(1)

    if not aim_path.is_dir():
        print(f"ERROR: AIMForScale folder not found at {aim_path}")
        print("  Clone it first: git clone https://github.com/francescafadel/AIMForScale.git")
        print("  Or run: python push_adb_to_github.py /path/to/AIMForScale")
        sys.exit(1)

    aim_adb = aim_path / "ADB"
    aim_adb.mkdir(parents=True, exist_ok=True)

    for name in ["README.md", "CONTENTS.md"]:
        src = LOCAL_ADB / name
        if src.is_file():
            shutil.copy2(src, aim_adb / name)
            print(f"Copied {name} -> {aim_adb / name}")

    links_src = LOCAL_ADB / "ADB Links"
    links_dst = aim_adb / "ADB Links"
    if links_src.is_dir():
        links_dst.mkdir(parents=True, exist_ok=True)
        readme = links_src / "README.md"
        if readme.is_file():
            shutil.copy2(readme, links_dst / "README.md")
            print(f"Copied ADB Links/README.md")

    pde_src = LOCAL_ADB / "Project Description Extraction"
    pde_dst = aim_adb / "Project Description Extraction"
    if pde_src.is_dir():
        if pde_dst.exists():
            shutil.rmtree(pde_dst)
        shutil.copytree(pde_src, pde_dst)
        print(f"Copied full Project Description Extraction/ -> {pde_dst}")
    else:
        print(f"WARNING: Project Description Extraction not found at {pde_src}")

    print("\n" + "=" * 60)
    print("Next steps — run these in your terminal:")
    print("=" * 60)
    print(f"  cd {aim_path}")
    print("  git add ADB/")
    print("  git status")
    print("  git commit -m \"Add ADB Project Description Extraction: scripts, tests, data, docs\"")
    print("  git push origin main")
    print("=" * 60)


if __name__ == "__main__":
    main()
