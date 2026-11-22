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

## Printer and filament

Before anything else, know the printer and the filament of every plate. Never assume them.

- Read `printer` and `filaments` from `layout.json`. If Alex named a printer or filament in the request, that wins: update `layout.json`.
- If the printer is missing, ask Alex which printer and nozzle.
- If a plate has no filament entry, ask Alex per plate: material type (PLA, PLA+, PETG, PETG matte, ...), colour, and brand if it is not Bambu. Ask all missing ones in one question round.
- Write the answers into `layout.json`: `printer`, and per plate `material`, `colour` and the Bambu Studio `preset` name that fits. Pick the preset from `~/Library/Application Support/BambuStudio/system/BBL/filament/`; if no preset matches the brand, use the `Generic <type>` one and say so.
- Use the printer for the Fillet bed check: the design's printer (`get_design`) must be the same model.
- Compare with the Bambu project (`printer_settings_id`, `filament_settings_id`, `filament_colour` in `Metadata/project_settings.config`, and each object's `extruder` in `Metadata/model_settings.config`). If they differ from `layout.json`, do not edit the settings in the file: tell Alex exactly which printer, filament slot, preset and colour to set in Bambu Studio and to save. A material printed with the wrong profile gives bad fit (seen 2026-11-22: PETG sliced as PLA came out loose).

## New model, first run

A model that has no folder yet cannot go through the project build, because there is no Bambu project to update.

1. Create the folder `YYYY-MM-DD-<name>/` in the repo root, date of today.
2. Ask printer and filaments as described above.
3. Work out the lay-flat move of every body (flat side down, lowest z = 0, bodies of one plate not overlapping) and group bodies into plates by colour. Write `layout.json` with `design`, `source`, `printer`, `filaments`, `plates`, `moves`; leave `project` out for now. Use the axolotl's `layout.json` as the pattern.
4. Run steps 1 to 6 below, then commit and push.
5. Tell Alex to do once in Bambu Studio: import all plate files of the folder, put each on its own plate, set printer and one filament per plate as recorded in `layout.json`, and save the project into the model folder. I do not open Bambu Studio for this.
6. When Alex says it is saved: add the file name as `project` to `layout.json`, check it against printer and filaments, commit and push.

From then on the normal steps apply.

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
   It swaps the shapes of each part by the source file recorded in the project and keeps plates, positions, filaments and settings. Read its report: parts on unchanged plates must show the same face count and a bounds change of 0; changed parts must show what is expected. Last line is `PROJECT CHANGED: <file>` or `PROJECT UNCHANGED`. Do not copy yet.
8. **Unsaved check**, only if the project changed and Bambu Studio is running:
   ```
   python3 -I .claude/skills/print-plates/bambu_unsaved.py "<model>/<project>"
   ```
   It compares the settings Bambu Studio holds right now with the saved project. If it lists differences, stop and show them to Alex: closing Bambu Studio would lose them. Otherwise copy the build output over the project file.
9. **Commit and push** on the current branch: one Conventional Commits message, multiline, no co-author line. After pushing, verify with `git fetch origin && git merge-base --is-ancestor HEAD origin/<branch>`. If `git status` shows nothing, there is nothing to commit: say so and skip step 10.
10. **Reopen Bambu Studio**, only if the project file changed.
   ```
   .claude/skills/print-plates/reopen_bambu.sh "<model>/<project>"
   ```
   It records the window position, quits Bambu Studio, writes that position into Bambu Studio's settings, opens the project and checks that one window sits in the same place. If Bambu Studio is not running it just opens the project.
11. **Report**: what changed per part, commit id, window position before and after, and what was not verified. I cannot see inside Bambu Studio, so ask Alex to confirm plates and to slice.

## Bambu Studio rules

- Never run `open` on Bambu Studio while an instance is running, with or without `-n`. It always spawns a second window on this machine. Only `reopen_bambu.sh` may open it.
- The window must come back in the same place on the same monitor.
- Quitting discards unsaved changes in Bambu Studio. Step 8 checks for them; never skip it before closing.
- Print settings and filaments in the project belong to Alex. The build only replaces shapes.
- Do not edit print settings inside the project file. On load Bambu Studio applies its own preset values by preset name again, so such edits are silently dropped (seen 2026-11-22: wall speeds written into the file came back as the preset's 200/300). Choosing a different filament preset by name does work. A setting that must differ from the preset has to be changed by Alex in Bambu Studio and saved there.

## When to stop and ask

- A body was added or removed.
- Print check fails.
- More than one Bambu Studio is running.
- Bambu Studio may hold unsaved changes.
- The build report shows a change on a part that was not supposed to change.

## Fit tuning

Fit of printed parts is tuned with design parameters in Fillet (`set_parameter`), then this skill is run again. For the axolotl: `stud_d`, `clr`, `wall`, `tube_od` for all bricks, `pink_grip` for the pink parts, `eye_clr` for the eye plugs.
