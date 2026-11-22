# 3dprint

3D-print models designed with Claude Code in Fillet and printed through Bambu Studio.

## The `3d-print` skill

One guided path from a description to a finished print. Claude asks, designs, exports and keeps git in order; you decide, slice, print and report.

| Phase | What happens | Your part |
|---|---|---|
| 0 Setup | Checks Fillet connection, file access, git | fix what it names |
| 1 Brief | Asks what is missing: object, size, style, colours, printer, filament, how parts join | answer |
| 2 Design | Builds the model in Fillet, shows renders | say "ok" or what to change |
| 3 Record | Stores printer and filament per colour | nothing |
| 4 Export | Lays parts flat, checks fit on the bed, exports one file per colour | nothing |
| 5 Bambu project | First time: guides you click by click. Later: puts new shapes into your project | first time: set up and save |
| 6 Save | Commits, pushes, reopens Bambu Studio in the same place | nothing |
| 7 Print | Tells you which spool per plate and how to assemble; asks how each joint fits; tunes and repeats | slice, print, report fit |

## How to use it

Start Claude Code in this folder, with Fillet running. Then just say what you want, or type `/3d-print`.

- **New model**: "I want a phone stand for A1 mini, black PETG." Missing details get asked.
- **Change a model**: "make the axolotl eyes bigger."
- **After a print**: "pink parts are loose." The fit gets tuned and re-exported.
- **Keep the result**: "save."

Claude stops and waits for you after the brief, after each design, before closing Bambu Studio with unsaved settings, and after sending you to print.

## What you find in a model folder

Folders are named `YYYY-MM-DD-<name>`.

| File | What |
|---|---|
| `<name>.fillet` | editable design |
| `plateN-<colour>.3mf` | shapes per colour |
| `<Name>.3mf` | Bambu Studio project |
| `layout.json` | printer, filaments, which part on which plate |

## Good to know

- Change print settings and filaments in Bambu Studio and save there. Edits made to the project file by hand are dropped by Bambu Studio.
- A new or removed part needs one manual import in Bambu Studio; the skill guides you.
- The skill closes and reopens Bambu Studio, one window, same place. It stops first if Bambu Studio holds unsaved settings.
- Terminal needs Full Disk Access (System Settings > Privacy & Security), otherwise Fillet's exports cannot be read.
- A loose or tight fit is most often a wrong filament profile. Check that before changing the design.

Skill files: `.claude/skills/3d-print/`.
