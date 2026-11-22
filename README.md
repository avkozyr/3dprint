# 3dprint

3D-print models designed with Claude Code in Fillet and printed through Bambu Studio.

## What the `print-plates` skill does

After a design change it takes the model from Fillet to a ready Bambu Studio project:

1. Asks for printer and filament per colour, if not known yet.
2. Lays every part flat and checks that it fits the printer.
3. Exports one file per colour (one spool per plate, no AMS).
4. Puts the new shapes into the Bambu Studio project. Plates, filaments and print settings stay as you saved them.
5. Commits and pushes.
6. Reopens Bambu Studio with the project: one window, same place as before.

You slice, print and swap spools.

## How to use it

Start Claude Code in this folder, with Fillet running.

**Change an existing model**

1. Say what to change, e.g. "pink parts are loose" or "make the eyes bigger".
2. Look at the result in Fillet. Say "ok".
3. Type `/print-plates`, or say "save".
4. In Bambu Studio: slice and print each plate.
5. Report the fit. Repeat from 1 if needed.

**Start a new model**

1. Describe the model, the printer and the filament per colour. Anything missing gets asked.
2. Approve the design in Fillet, then `/print-plates`.
3. One time only, in Bambu Studio: import the plate files from the model folder, one plate per colour, set printer and filaments, save the project into the model folder.
4. Say "saved". From now on the model works like an existing one.

## What you find in a model folder

| File | What |
|---|---|
| `<name>.fillet` | editable design |
| `plateN-<colour>.3mf` | shapes per colour |
| `<Name>.3mf` | Bambu Studio project |
| `layout.json` | printer, filaments, which part on which plate |

## Good to know

- Change print settings and filaments in Bambu Studio and save there. Edits made to the project file by hand are dropped by Bambu Studio.
- A new or removed part needs one manual import in Bambu Studio; the skill stops and says so.
- The skill closes and reopens Bambu Studio. It stops first if Bambu Studio holds unsaved settings.
- Terminal needs Full Disk Access (System Settings > Privacy & Security), otherwise Fillet's exports cannot be read.
- Fit is tuned through design parameters. Axolotl: `pink_grip` for the pink parts, `eye_clr` for the eyes, `stud_d` and `clr` for all bricks.

Skill files: `.claude/skills/print-plates/`.
