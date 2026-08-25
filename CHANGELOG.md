# Changelog

All notable changes to dwatcher are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.0.0] - 2026-08-25

First polished release: standalone `.exe`, native GUI, full CLI.

### Added
- Native tkinter GUI (`dwatcher gui`): live status, per-category stats bars,
  recent-moves table, pause/resume, dry-run toggle.
- Standalone Windows executable via PyInstaller — no Python required on the
  target machine.
- `--version` flag on the CLI.
- Continuous watch mode with exponential backoff and JSONL event logging.
- Crash recovery: write-ahead intent journal; `recover` finishes or rolls
  back interrupted moves.
- Per-category move statistics (`stats`) backed by SQLite history.
- Custom rules in `dwatcher.toml`: remap extensions or opt them out (`[]`).
- Launcher scripts: `dwatcher-sort.bat`, `dwatcher-watch.bat`, `dwatcher-gui.bat`.

### Safety
- In-flight downloads (`.crdownload`, `.part`, `.download`, `.opdownload`,
  `.tmp`) are never touched; size/quiet-time stability check before moving.
- Collision-safe moves — existing files get ` (1)`, ` (2)`… suffixes.
- Dry-run mode for every destructive operation.

### Fixed
- Built exe previously used `console=False`, which silenced all CLI
  subcommands; now console is enabled for CLI use and hidden only for GUI.

## [0.1.0] - 2026-08-22

Initial development releases: core classification, stability detection,
collision-safe mover, scanner pipeline, SQLite store + journal, recovery,
watch loop, TOML config, CLI — built test-first (73 tests).
