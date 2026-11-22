#!/bin/zsh
set -e

project=$1
here=${0:A:h}
conf="$HOME/Library/Application Support/BambuStudio/BambuStudio.conf"
bounds=""

running=($(pgrep -i bambustudio || true))
if (( ${#running} > 1 )); then
    echo "More than one Bambu Studio is running: ${running[*]}. Close the extra ones first."
    exit 1
fi

if (( ${#running} == 1 )); then
    bounds=$(swift "$here/bambu_window.swift" ${running[1]})
    echo "window before: $bounds"
    osascript -e 'tell application "BambuStudio" to quit'
    for attempt in {1..30}; do
        pgrep -i bambustudio >/dev/null || break
        sleep 1
    done
    if pgrep -i bambustudio >/dev/null; then
        echo "Bambu Studio did not quit, it may be asking to save. Nothing was opened."
        exit 1
    fi
fi

if [[ -n "$bounds" ]]; then
    python3 -I - "$conf" "$bounds" <<'EOF'
import json
import re
import sys

path, bounds = sys.argv[1:3]
text = open(path).read()
updated, count = re.subn(r'("window_mainframe":\s*")[^"]*(")', lambda m: m.group(1) + bounds + m.group(2), text)
if count != 1:
    raise SystemExit("window_mainframe not found exactly once in Bambu Studio settings")
json.loads(updated)
open(path, "w").write(updated)
EOF
fi

open -a BambuStudio "$project"

after=""
for attempt in {1..15}; do
    sleep 8
    pid=$(pgrep -i bambustudio | head -1)
    after=$(swift "$here/bambu_window.swift" $pid 2>/dev/null || true)
    [[ -z "$bounds" && -n "$after" ]] && break
    [[ -n "$bounds" && "$after" == "$bounds" ]] && break
done

echo "window after:  $after"
echo "instances: $(pgrep -i bambustudio | wc -l | tr -d ' ')"
if [[ -n "$bounds" && "$after" != "$bounds" ]]; then
    echo "Window position does not match."
    exit 1
fi
