# Download Watcher (`dwatcher`)

Watches a folder (default: your Downloads) and auto-organizes **completed**
downloads into category folders — safely.

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

## Install

```bash
# from the project folder
uv venv .venv
uv pip install -e . --python .venv/Scripts/python.exe
```

No third-party runtime dependencies — Python 3.11 stdlib only.

## Usage

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

Or just double-click `dwatcher-sort.bat` (one-shot) / `dwatcher-watch.bat`.

## Configuration (`dwatcher.toml`)

```toml
[watch]
dir = "C:/Users/Temp/Downloads"   # folder to watch
dest = ""                          # omit = sort in place
interval = 10                      # seconds between scans (watch mode)
quiet_seconds = 30                 # file must be unchanged this long
dry_run = false

[rules]                            # optional custom rules
".stl" = "3DPrints"
".txt" = []                        # [] = never touch .txt files
```

## Development

```bash
.venv\Scripts\python.exe -m pytest -q     # 73 tests
```

Architecture: `rules` (classify) · `stability` (is it done?) ·
`mover` (collision-safe moves) · `scanner` (pipeline) ·
`store` (SQLite history + intent journal) · `recovery` (crash repair) ·
`watcher` (loop + backoff + JSONL logs) · `cli`.
