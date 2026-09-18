# Download Watcher — Full Health Overhaul: Change Specification

Branch: `plan/full-health-overhaul` (11 commits on top of `main` @ `4bedb09`).
Suite: **95 tests passing** (`python -m pytest -q`), up from 74. Zero runtime dependencies preserved (stdlib only).

## 1. Why

A codebase survey found live bugs: every real move recorded `size=0`; `watch --watch DIR`
silently ignored; GUI Recover crashed (`tk.messagebox` never imported); recovery deleted
the wrong copy on collision and aborted the whole journal on one locked file; custom
`[rules]` wiped all defaults; `dest = ""` sorted files into the process CWD. Plus
robustness gaps (SQLite `database is locked` under threads, unbounded log, dead
size-tracking) and doc drift (README promised a GUI dry-run toggle that didn't exist).

## 2. Behavior changes (read before merging)

1. **Custom `[rules]` now MERGE over defaults** (`rules.resolve_rules()`). Previously any
   `[rules]` table *replaced* every builtin. `[]` still opts an extension out. Users with
   a full custom table will now also get builtin categories they didn't list.
2. **`dest = ""` now means "sort in place"** (was: `Path(".")` = process CWD — a footgun).
   Omit the key or leave it empty; both yield `dest_root = watch_dir`.
3. **Invalid config is loud**: negative `interval`/`quiet_seconds`, non-int values,
   non-table `[rules]`, and unreadable files raise `ValueError` (CLI surfaces negatives
   as `error: --quiet must be >= 0`, exit via `SystemExit`).
4. **`--db`/`--log` resolve relative to the `--config` file's directory** (was: always CWD).
   No flag + no config → CWD defaults unchanged. New `watch --log PATH` flag.
5. **`once` exit code**: any errors with zero moves → exit 1 (was: only "cannot list" with
   `scanned == 0`). Message unchanged.
6. **Recovery is conservative**: both-sides-present with *different* content no longer
   deletes `src` — it re-homes it to a ` (n)` collision name. Same size+mtime still
   dedupes. Every intent is isolated: one failure can't abort the rest. New
   `recover_pending(store, dry_run=False)`; dry-run reports `would …` and changes nothing.
7. **Watcher log**: failures to write `dwatcher_events.jsonl` no longer fail scans or
   trigger backoff; log rotates to `.jsonl.1` past 1 MB. `Watcher` keeps `previous_sizes`
   across cycles, so the documented size-growth check actually runs.
8. **GUI**: Recover dialog works; Open-folder works off-Windows; manual scan no longer
   drops watcher updates; dry-run is a real checkbox (README claim now true); file sizes
   render `512 B` not `512.0 B`; `.partial`/`.temp` count as in-flight downloads.

## 3. Module-by-module changes

| Module | Change |
|---|---|
| `config.py` | `dest ""→None`; int validation + `>= 0`; `OSError`/`UnicodeDecodeError` → `ValueError`; `[rules]` must be a table |
| `rules.py` | New `normalize_ext()` + `resolve_rules(custom)` (merge, `[]` opt-out, type checks); `classify()` uses it |
| `scanner.py` | Size stat'ed **before** move (fixes `size=0`); clears **final** `result.dst` intent **and** `plan.dst` on collision; accepts/updates `previous_sizes`; `resolve_rules()` |
| `stability.py` | `PARTIAL_SUFFIXES` += `.partial`, `.temp` |
| `store.py` | `Store(path, timeout=30.0)`, `check_same_thread=False`, `WAL` + `synchronous=NORMAL`, `idx_intents_src`, per-instance `threading.Lock` on all methods, idempotent `close()`, ctx manager |
| `mover.py` | `Path` types end-to-end, `MAX_COLLISIONS=10000` (was: unbounded loop) |
| `recovery.py` | `import os` (was `shutil.os`); per-intent `try/except Exception`; size+mtime compare before delete; reuses `mover.unique_destination`; `dry_run` flag; clears renamed intents |
| `watcher.py` | Guarded `_log` + 1 MB rotation; `previous_sizes` wired into `scan_once`; safe category derivation; `log_max_bytes` param |
| `cli.py` | Fixed `watch --watch` (`watch_dir` attr); negative `--quiet/--interval` rejected; `_db_path`/`_log_path` config-relative; fixed `once` error logic |
| `gui.py` + new `gui_state.py`, `gui_thread.py`, `gui_utils.py` | Split 414-line god-file; single shared `Store`; separate `manual_queue` (no more dropped updates); `messagebox` import; cross-platform `open_folder()`; dry-run Checkbutton; `format_size()` (`512 B`); `token_lines()`; `status` header unchanged otherwise |
| `dwatcher.example.toml` | `dest` commented-out pattern + opt-out example |
| `README.md` | Omit-dest docs, `dwatcher-gui.bat`, non-recursive scan, collisions, `--db/--log`, rotation, real test count |
| `CHANGELOG.md` | `[Unreleased]` section |
| New `dwatcher-gui.bat`, `.github/workflows/pytest.yml` | GUI launcher; Windows CI (`setup-python 3.11` + `pytest`) |

## 4. Tests (74 → 95, all green)

New/strengthened per file: `test_config` (empty-dest, negative, unreadable),
`test_rules` (merge, opt-out, bad-type), `test_scanner` (nonzero size + intent cleared,
growth blocked, no orphan intent on collision), `test_store` (idempotent close, ctx
manager, 4-thread × 25 concurrent writes), `test_mover` (Path types, collision name),
`test_recovery` (different-size keeps both + dst intact, locked file doesn't abort rest),
`test_cli` (watch override, negative rejected), `test_watcher` (log failure still `ok`
**with a real move attempted**, sizes tracked), `test_gui` (format, open-folder fallback,
state toggle, token lines). Full suite run before every commit; final whole-branch
review: APPROVED-WITH-MINORS, all Important findings fixed in `de6bdc4` and re-verified.

## 5. Verify after checkout

```bash
.venv\Scripts\python.exe -m pytest -q          # 95 passed
.venv\Scripts\python.exe -m dwatcher.cli once --dry-run   # preview, moves nothing
.venv\Scripts\python.exe -m compileall -q src/dwatcher
```

## 6. Notes / follow-ups (not in scope)

- GUI launch never verified headless here (no display) — smoke-test `dwatcher gui` once.
- `dwatcher_events.jsonl` / `*.db` are tracked runtime artifacts in the repo; untouched by
  this branch but worth untracking separately.
- Parked micro-nits (accepted): same-file heuristic is size+mtime only; `_log` guards
  `OSError`; CLI error message is broad (exit code is exact); `previous_sizes` retains
  unclassified entries until restart.
