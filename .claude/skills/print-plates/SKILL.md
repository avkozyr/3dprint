---
name: print-plates
description: After a design change in Fillet, export the print plates, update the Bambu Studio project, commit and push, and reopen Bambu Studio in the same place. Use when Alex says the design is ok to print, asks to export or update plates, or says "save" after a change to a model in this repo.
---

# print-plates

Turns the design that is open in Fillet into updated files in the model folder and an updated Bambu Studio project. Alex only slices, prints and swaps spools.

Each model has its own folder in the repo with:

- `layout.json`: which bodies go on which plate file, and the move that lays each body flat for printing
- `<name>.fillet`: design source
- `plateN-<colour>.3mf`: one file per colour, Alex prints without AMS, one spool per plate
- the Bambu Studio project named in `layout.json`: plates, filaments and print settings

## Before starting

- Fillet tools (`mcp__fillet__*`) must be connected and the design named in `layout.json` must be the current one (`list_designs`, `select_design`).
- `get_design`: every step must have status ok. If not, stop and report.
- Compare the bodies in the design with the bodies in `layout.json`. If a body was added or removed, stop: the project build only swaps shapes of existing parts. A new part needs a move in `layout.json` and one manual import in Bambu Studio by Alex, then a save.
- Terminal needs Full Disk Access, otherwise Fillet's container cannot be read.

## Steps

1. **Lay flat.** For every body in `layout.json` `moves`, call `move_bodies` with that rotate/translate and the step name `Plate layout <body>`. Every body must end with lowest z = 0.
2. **Print check.** `check_print` once per plate with that plate's bodies. Must fit the bed and be watertight. On failure, remove the layout steps and stop.
3. **Export plates.** One `export` (format `3mf`) per plate, one call at a time, to `~/Library/Containers/app.fillet.Fillet/Data/tmp/<plate file name>`. Fillet is sandboxed and can only write there. Never export two plates in parallel or to the default path, they overwrite each other.
4. **Restore pose.** `delete_feature` every `Plate layout <body>` step. `get_design` must show the same step count as before step 1.
5. **Export source.** `export` format `fillet` to the same container folder, with the source file name from `layout.json`.
6. **Move files** into the model folder. For each plate, compare `3D/3dmodel.model` inside the new and the old file: if identical, delete the new one and keep the old file, so git shows only real changes. Always move the `.fillet` file. Leave nothing of ours in the container folder.
7. **Build project.** Run from the repo root:
   ```
   python3 -I .claude/skills/print-plates/build_bambu_project.py "<model>/<project>" "<model>" "<scratchpad>/project-out.3mf"
   ```
   It swaps the shapes of each part by the source file recorded in the project and keeps plates, positions, filaments and settings. Read its report: parts on unchanged plates must show the same face count and a bounds change of 0; changed parts must show what is expected. Then copy the output over the project file.
8. **Commit and push** on the current branch: one Conventional Commits message, multiline, no co-author line. After pushing, verify with `git fetch origin && git merge-base --is-ancestor HEAD origin/<branch>`.
9. **Reopen Bambu Studio.**
   ```
   .claude/skills/print-plates/reopen_bambu.sh "<model>/<project>"
   ```
   It records the window position, quits Bambu Studio, writes that position into Bambu Studio's settings, opens the project and checks that one window sits in the same place. If Bambu Studio is not running it just opens the project.
10. **Report**: what changed per part, commit id, window position before and after, and what was not verified. I cannot see inside Bambu Studio, so ask Alex to confirm plates and to slice.

## Bambu Studio rules

- Never run `open` on Bambu Studio while an instance is running, with or without `-n`. It always spawns a second window on this machine. Only `reopen_bambu.sh` may open it.
- The window must come back in the same place on the same monitor.
- Quitting discards unsaved changes in Bambu Studio. Before step 9, look at the session folder under `$TMPDIR/bamboo_model/<day>/*#<pid>#*`: if files there are newer than the project file, Alex may have unsaved work. Say so and ask before closing.
- Print settings and filaments in the project belong to Alex. The build only replaces shapes.

## When to stop and ask

- A body was added or removed.
- Print check fails.
- More than one Bambu Studio is running.
- Bambu Studio may hold unsaved changes.
- The build report shows a change on a part that was not supposed to change.

## Fit tuning

Fit of printed parts is tuned with design parameters in Fillet (`set_parameter`), then this skill is run again. For the axolotl: `stud_d`, `clr`, `wall`, `tube_od` for all bricks, `pink_grip` for the pink parts, `eye_clr` for the eye plugs.
