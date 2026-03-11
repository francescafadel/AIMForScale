# How to get Project Description Extraction onto GitHub

On GitHub you only see **ADB → ADB Links** (3 files). The **Project Description Extraction** folder (all our scripts, tests, data, docs) is only on your computer. Follow these steps to add it.

---

## Why it might look like "nothing" is there

1. **The new folder was never copied into AIMForScale**  
   The code lives in `ADB Project Description Extraction/ADB/Project Description Extraction/`. That whole folder must be copied *into* your AIMForScale repo at `AIMForScale/ADB/Project Description Extraction/`. If you only opened or pushed a different folder, GitHub never gets it.

2. **AIMForScale is in a different place**  
   The script assumes AIMForScale is at `~/Desktop/AIMForScale`. If it's in Documents or elsewhere, the copy goes nowhere you push from. Use the path in **Option B** or **COPY_PASTE_COMMANDS.txt**.

3. **Git isn't adding the new files**  
   After copying, you must run `git add ADB/` and `git status` *inside the AIMForScale folder*. If you run them in "ADB Project Description Extraction" (which isn't a git repo for AIMForScale), nothing gets pushed. Always `cd` into AIMForScale first.

4. **.gitignore in AIMForScale**  
   If `git status` shows no new files under ADB after copying, check:  
   `cat AIMForScale/.gitignore`  
   If `ADB` or `*.csv` or similar is ignored, those files won't be added. You can force-add once:  
   `git add -f ADB/Project\ Description\ Extraction/`

**Files in this folder that help:**  
- **COPY_PASTE_COMMANDS.txt** — Terminal commands you can copy-paste (no Python).  
- **DIAGNOSE_AND_PUSH.py** — Runs a quick check (paths, copy, then `git status` inside AIMForScale).  
- **push_adb_to_github.py** — Copies this ADB content into AIMForScale.

---

## Option A: Use the script (easiest)

1. **Clone AIMForScale** (if you don’t already have it):
   ```bash
   cd ~/Desktop
   git clone https://github.com/francescafadel/AIMForScale.git
   ```

2. **Run the copy script** from the folder that *contains* the ADB folder (e.g. "ADB Project Description Extraction"):
   ```bash
   cd "/Users/francesca/Desktop/ADB Project Description Extraction"
   python3 "ADB/Project Description Extraction/push_adb_to_github.py"
   ```
   Or from inside this folder: `python3 push_adb_to_github.py` (script will look for parent/ADB).

   If AIMForScale is elsewhere: `python3 push_adb_to_github.py /path/to/AIMForScale`

3. **Then run the git commands the script prints** (cd to AIMForScale, git add, commit, push).

4. On GitHub, open **ADB** — you should see **Project Description Extraction** (and README.md, CONTENTS.md) in addition to **ADB Links**.

---

## Option B: Copy manually

1. Clone AIMForScale if needed.
2. Copy the entire **ADB** folder from your local project into `AIMForScale/ADB/` (so you have `AIMForScale/ADB/README.md`, `ADB/CONTENTS.md`, `ADB/Project Description Extraction/`, `ADB/ADB Links/`).
3. From AIMForScale: `git add ADB/` then `git commit` and `git push origin main`.

---

## If it still doesn’t show up

- Run `git status` inside AIMForScale after copying. You should see `ADB/Project Description Extraction/` and other new files under `ADB/`.
- If you only see changes in `ADB Links/`, the **Project Description Extraction** folder wasn’t copied. Copy it again.
