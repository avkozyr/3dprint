---
name: print-model
description: Full path from a description of a 3D-print model to a finished print - asks the missing questions, designs in Fillet, exports plates per colour, sets up or updates the Bambu Studio project, guides Alex through slicing, printing and assembly, tunes fit from feedback, and keeps everything in git. Use when Alex describes something to print, wants to change or reprint a model in this repo, reports how a print fits, or says "save".
---

# print-model

One guided path: description, questions, design, export, Bambu Studio, print, fit feedback, git.

Alex decides and prints. I ask, design, export, keep files and git in order, and say at every manual step exactly what to click. Work in phases, in order. At each **STOP** wait for Alex's answer. Start at the phase that fits: a new description starts at phase 1, a change to an existing model at phase 2, a fit report at phase 7.

Each model lives in its own folder `YYYY-MM-DD-<name>/` in the repo root:

| File | What |
|---|---|
| `layout.json` | printer, filament per plate, which body on which plate, lay-flat move per body |
| `<name>.fillet` | design source |
| `plateN-<colour>.3mf` | shapes per colour |
| `<Name>.3mf` | Bambu Studio project: plates, filaments, print settings |

The axolotl folder is the worked example for all of them.

## Phase 0: setup check

Check quietly, speak only about what fails, and then guide the fix:

- **Fillet connected**: `mcp__fillet__list_designs` answers. If the tools are missing: Fillet must be running (its start panel is normal, click New Document), agent connections allowed in Fillet, then `claude mcp add --transport http fillet http://127.0.0.1:7878/mcp` and `/mcp` to connect.
- **Fillet's exports readable**: `ls ~/Library/Containers/app.fillet.Fillet/Data/tmp`. `Operation not permitted` means Terminal lacks Full Disk Access (System Settings > Privacy & Security). Alex must switch it on and restart Terminal.
- **Git**: repo clean, note the current branch. Never create or switch branches.

## Phase 1: brief

Find out what to build. Never assume; ask only what the request did not answer. Ask in rounds of at most four questions, concrete options, recommended one first, each with its trade-off.

Needed before any design:

1. **Object**: what it is and what it is for (figure, holder, bracket, ...). Unclear words: say how I read them and ask.
2. **Size**: rough overall size, and anything it must fit onto or into, with measures.
3. **Style and must-haves**: look, and hard requirements such as fitting real bricks, a screw size, a load.
4. **Colours**: which colours, and which part gets which.
5. **Printer**: model and nozzle.
6. **Filament per colour**: material type (PLA, PLA+, PETG, PETG matte, ...) and brand if not Bambu.
7. **Multi-colour method**: AMS in one print, or separate parts per colour on separate plates. This changes the design.
8. **How parts join**, when printed separately: snap fit, press fit, or glue.

Then state the plan in a few lines: parts, colours, sizes, how they join, what is tunable. **STOP** for Alex's ok.

## Phase 2: design in Fillet

- New model: `new_design` with the printer preset and a name. Never touch another open design. Existing model: make it current (`list_designs`, `select_design`); if it is not open, tell Alex to open the `.fillet` file from the model folder in Fillet.
- One body per printed part. Body colour in Fillet = filament colour; it decides the plate.
- Every dimension that decides fit is a named parameter with a comment (`set_parameter`), never a bare number. Parts of a material that prints differently get their own fit parameter.
- Design for printing without supports: every part has a flat side to lie on; parts of another colour join mechanically (studs, pegs, plates), not by floating in place.
- Changing an existing step: `get_feature`, then `edit_feature`. Do not rebuild what can be edited.
- Check before showing: `get_design` all steps ok; `render_view` of the whole model with `show_user: true`; a section render through every joint to see that parts meet and do not collide.
- Tell Alex what was built, which choices I made on my own, and what is not verified. **STOP** until Alex says the design is ok. Repeat this phase for every change request.

## Phase 3: printer and filament record

Printer and filament of every plate must be known and written down. Never assume them.

- Read `printer` and `filaments` from `layout.json`. What Alex said in this conversation wins: update the file.
- Anything missing: ask (phase 1, points 5 and 6), all in one round.
- Per plate store `material`, `colour` and the Bambu Studio `preset` name. Pick the preset from `~/Library/Application Support/BambuStudio/system/BBL/filament/`; no preset for the brand: use `Generic <type>` and say so.
- The Fillet design's printer (`get_design`) must be the same model.

## Phase 4: export plates

New model first: create the folder, group bodies into plates by colour, work out the lay-flat move of every body (flat side down, lowest z = 0, bodies of one plate not overlapping), and write `layout.json` with `design`, `source`, `printer`, `filaments`, `plates`, `moves`. No `project` entry yet.

Existing model: compare the design's bodies with `layout.json`. A body added or removed: update `layout.json`, and remember it for phase 5.

Then:

1. **Lay flat.** For every body in `moves`, `move_bodies` with that rotate/translate, step name `Plate layout <body>`. Every body must end with lowest z = 0.
2. **Print check.** `check_print` once per plate with that plate's bodies. Must fit the bed and be watertight. On failure remove the layout steps and stop.
3. **Export plates.** One `export` (format `3mf`) per plate, one call at a time, to `~/Library/Containers/app.fillet.Fillet/Data/tmp/<plate file name>`. Fillet is sandboxed and can write only there. Never export two plates in parallel or to the default path: they overwrite each other.
4. **Restore pose.** `delete_feature` every `Plate layout <body>` step. Step count must equal the count before step 1.
5. **Export source.** `export` format `fillet` to the same folder, with the source name from `layout.json`.
6. **Move files** into the model folder. Per plate, compare `3D/3dmodel.model` inside new and old file: identical means delete the new one and keep the old, so git shows only real changes. Always move the `.fillet`. Leave nothing of ours in Fillet's folder.

## Phase 5: Bambu Studio project

**No project yet (new model).** Commit and push what exists, then guide Alex, one numbered step at a time, to do this once in Bambu Studio. I do not open Bambu Studio for it.

1. Select the printer and nozzle from `layout.json`.
2. Import all plate files of the model folder (File > Import, select them together).
3. Add plates (`+`) until there is one per plate file. Each imported file is one object; put each on its own plate. Press `A` on a plate if parts overlap. Do not rotate parts, they already lie flat.
4. Filaments: one slot per plate, with the preset and colour from `layout.json`. Read them out to Alex as a list.
5. Right-click each object > Change Filament > its slot.
6. Save the project into the model folder.

**STOP** until Alex says it is saved. Then add the file name as `project` to `layout.json`.

**Project exists.**

1. Build: from the repo root
   ```
   python3 -I .claude/skills/print-model/build_bambu_project.py "<model>/<project>" "<model>" "<scratchpad>/project-out.3mf"
   ```
   It swaps the shape of every part by the source file recorded in the project and keeps plates, positions, filaments and settings. Read the report: unchanged parts must show the same face count and bounds change 0, changed parts what is expected. Last line is `PROJECT CHANGED: <file>` or `PROJECT UNCHANGED`.
2. A body was added or removed: the build cannot do that. Guide Alex to import the new plate file or delete the object in Bambu Studio, assign plate and filament, and save. **STOP** until saved.
3. Unsaved check, if the project changed and Bambu Studio is running:
   ```
   python3 -I .claude/skills/print-model/bambu_unsaved.py "<model>/<project>"
   ```
   Differences listed: show them, **STOP**, and ask whether Alex saves first. No differences: copy the build output over the project file.

**Always, once a project exists:** check it against `layout.json`: `printer_settings_id`, `filament_settings_id`, `filament_colour` in `Metadata/project_settings.config`, and each object's `extruder` in `Metadata/model_settings.config`. A mismatch is never fixed in the file. Tell Alex which slot, preset and colour to set in Bambu Studio and to save. A material sliced with the wrong profile prints with bad fit.

## Phase 6: save and reopen

1. Commit on the current branch: Conventional Commits, multiline, no co-author line. Push, then verify with `git fetch origin && git merge-base --is-ancestor HEAD origin/<branch>`. Nothing changed: say so, no commit.
2. Only if the project file changed:
   ```
   .claude/skills/print-model/reopen_bambu.sh "<model>/<project>"
   ```
   It records the window position, quits Bambu Studio, restores the position, opens the project and checks that one window sits in the same place.

## Phase 7: print, assemble, tune

Guide the print. Give Alex this as a short list:

- per plate, in order: plate number, parts on it, which spool to load, the preset that must show in Bambu Studio, then Slice and Print
- how the printed parts go together, part by part
- what is still untested in this version

**STOP** until Alex reports. Then ask about every joint by name: too tight, good, or loose. One word per joint is enough.

- Loose or tight: first make sure the plate was sliced with the right filament profile; a wrong profile is the more likely cause. Only then change the fit parameter of that part in small steps (0.05 to 0.15 mm), go back to phase 2 with that one change, and run phases 4 to 7 again for the changed plate.
- All good: record the tuned parameter values in the commit message, and say the model is done.

Never call a fit verified that Alex has not printed and confirmed.

## Bambu Studio rules

- Never run `open` on Bambu Studio while an instance is running, with or without `-n`. It always spawns a second window on this machine. Only `reopen_bambu.sh` may open it.
- The window must come back in the same place on the same monitor.
- Quitting discards unsaved changes. Never close without the unsaved check.
- Do not edit print settings inside the project file. On load Bambu Studio applies its own preset values by preset name again, so such edits are silently dropped (seen 2026-11-22: wall speeds written into the file came back as the preset's 200/300). Choosing a different filament preset by name does work. A setting that must differ from the preset is changed by Alex in Bambu Studio and saved there.
- I cannot see inside Bambu Studio. What it shows, Alex has to confirm.

## When to stop and ask

- Something in the brief is missing or can be read two ways.
- Design plan or design not yet approved.
- Print check fails.
- A body was added or removed and Bambu Studio needs a manual step.
- More than one Bambu Studio is running, or it holds unsaved settings.
- The build report shows a change on a part that should not have changed.
- Project printer or filament differs from `layout.json`.

## What I report at the end of a run

What changed per part, commit id, Bambu Studio window position before and after, and plainly what was not verified.
