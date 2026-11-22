import glob
import json
import os
import subprocess
import sys
import tempfile
import zipfile

IGNORED = ("wipe_tower_x", "wipe_tower_y")


def session_folder():
    pids = subprocess.run(["pgrep", "-i", "bambustudio"], capture_output=True, text=True).stdout.split()
    if len(pids) != 1:
        return None
    found = glob.glob(os.path.join(tempfile.gettempdir(), "bamboo_model", "*", f"*#{pids[0]}#*"))
    return found[0] if found else None


def same(a, b):
    def number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value

    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(number(x) == number(y) for x, y in zip(a, b))
    return number(a) == number(b)


def differences(project_path):
    folder = session_folder()
    if folder is None:
        return None
    configs = sorted(glob.glob(os.path.join(folder, "_temp_*.config")), key=os.path.getmtime)
    if not configs:
        return {}
    saved = json.loads(zipfile.ZipFile(project_path).read("Metadata/project_settings.config"))
    live = json.load(open(configs[-1]))
    return {
        key: (saved.get(key), live.get(key))
        for key in sorted(set(saved) | set(live))
        if key not in IGNORED and not same(saved.get(key), live.get(key))
    }


if __name__ == "__main__":
    result = differences(sys.argv[1])
    if result is None:
        print("No single running Bambu Studio session found.")
    elif not result:
        print("Bambu Studio session matches the saved project.")
    else:
        print(f"{len(result)} settings differ between Bambu Studio and the saved project:")
        for key, (saved, live) in result.items():
            print(f"  {key}: saved {saved} | Bambu Studio {live}")
        sys.exit(2)
