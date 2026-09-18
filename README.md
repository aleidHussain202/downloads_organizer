# Download Watcher (`dwatcher`)

Watches a folder (default: your Downloads) and auto-organizes **completed**
downloads into category folders — safely.

**Current release:** [v1.0.0](CHANGELOG.md) · 93 tests, zero runtime dependencies.

## Quick start (no Python needed)

Copy `dist/dwatcher.exe` anywhere (~11 MB standalone) and run it:

```bash
dwatcher.exe gui              # native desktop app
dwatcher.exe once --dry-run   # preview a sort of your Downloads
dwatcher.exe once             # sort in place (creates category folders)
dwatcher.exe watch            # continuous watch (Ctrl+C to stop)
dwatcher.exe recover          # finish/rollback moves after a crash or kill
dwatcher.exe stats            # move counts per category
```

Double-clicking `dwatcher-gui.bat` / `dwatcher-sort.bat` /
`dwatcher-watch.bat` does the same from the project folder.

## What it looks like

```
Downloads/
├── SteamSetup.exe   → Downloads/Installers/SteamSetup.exe
├── manual.pdf       → Downloads/Documents/manual.pdf
├── photo.jpg        → Downloads/Images/photo.jpg
├── backup.zip       → Downloads/Archives/backup.zip   (or "backup (1).zip" on collision)
├── bigfile.iso.crdownload   → untouched (still downloading)
└── data.xyz                 → untouched (no rule)
```

## Safety features

- **Never touches in-flight downloads** — `.crdownload`, `.part`, `.download`,
  `.opdownload`, `.tmp` are skipped, plus a size/quiet-time check.
- **Collision-safe** — never overwrites; adds ` (1)`, ` (2)`… suffixes.
- **Dry run** — see what *would* happen without moving anything.
- **Crash-safe journal** — every move is pre-recorded in SQLite; if the
  process dies mid-move, `dwatcher recover` finishes or rolls back cleanly.
- **Audit trail** — full move history + JSONL event log.

## Install (from source)

```bash
# from the project folder
uv venv .venv
uv pip install -e . --python .venv/Scripts/python.exe
```

No third-party runtime dependencies — Python 3.11 stdlib only.

## Usage (from source)

```bash
# one-shot sort of your Downloads (in place)
.venv\Scripts\python.exe -m dwatcher.cli once

# preview without touching anything
.venv\Scripts\python.exe -m dwatcher.cli once --dry-run

# watch continuously (Ctrl+C to stop)
.venv\Scripts\python.exe -m dwatcher.cli watch --interval 10

# custom folders
.venv\Scripts\python.exe -m dwatcher.cli once --watch C:/Users/me/Drop --dest D:/Sorted

# after a crash / force-kill
.venv\Scripts\python.exe -m dwatcher.cli recover

# how many files sorted per category
.venv\Scripts\python.exe -m dwatcher.cli stats
```

Or run the same commands through `dist/dwatcher.exe` (see Quick start).

## GUI

```bash
dwatcher.exe gui [--config path/to/dwatcher.toml]
```

The GUI (dark theme, 4 tabs) shows a Dashboard with live status, session
counters and per-category stats bars; a Recent Moves table; an Activity log
of scans, notes and errors (last 200, in-memory); and a Settings tab with
the active config plus pause/resume and dry-run controls. It hides its
console window; the CLI subcommands keep theirs.

## Configuration (`dwatcher.toml`)

```toml
[watch]
dir = "C:/Users/Temp/Downloads"   # folder to watch
# dest = "D:/Sorted"   # omit this key = sort in place (do NOT use dest = "")
interval = 10                      # seconds between scans (watch mode)
quiet_seconds = 30                 # file must be unchanged this long
dry_run = false

[rules]                            # optional custom rules
".stl" = "3DPrints"
".txt" = []                        # [] = never touch .txt files
```

Omit `dest` entirely to sort in place (do NOT use `dest = ""`) —
`dest` is commented out in `dwatcher.example.toml`.

Scans cover top-level files only (non-recursive); collisions never
overwrite — they get ` (1)`, ` (2)` suffixes.

`--db` (history commands) and `--log` (`watch`) take a file path;
relative paths resolve against the config file's folder, else the working
directory. The watch JSONL event log rotates to `.jsonl.1` once over 1 MB.

## Development

```bash
.venv\Scripts\python.exe -m pytest -q     # 93 tests

# rebuild the exe after changes
.venv\Scripts\pyinstaller.exe dwatcher.spec
```

Architecture: `rules` (classify) · `stability` (is it done?) ·
`mover` (collision-safe moves) · `scanner` (pipeline) ·
`store` (SQLite history + intent journal) · `recovery` (crash repair) ·
`watcher` (loop + backoff + JSONL logs) · `cli` · `gui`.
