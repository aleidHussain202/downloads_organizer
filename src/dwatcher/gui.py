"""Native Windows GUI for dwatcher (tkinter, stdlib only)."""

from __future__ import annotations

import ctypes
import queue
import sys
import threading
import tkinter as tk
import tkinter.messagebox
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from .config import DEFAULTS, load_config
from .gui_state import GuiState
from .gui_theme import PALETTE, apply_theme
from .gui_thread import WatcherThread
from .gui_utils import format_size, open_folder, status_dot, stripe, summarize, token_lines
from .scanner import scan_once
from .store import Store


def _hide_console():
    """Hide the console window on Windows when running GUI mode."""
    if sys.platform == "win32":
        try:
            kernel32 = ctypes.windll.kernel32
            user32 = ctypes.windll.user32
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                user32.ShowWindow(hwnd, 0)  # SW_HIDE
        except Exception:
            pass


class DwatcherGui:
    """Main GUI application."""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or "dwatcher.toml"
        self.cfg = load_config(self.config_path)
        self.db_path = Path("dwatcher.db")
        self.store = Store(self.db_path, timeout=30.0)

        # State shared with watcher thread
        self.state = GuiState(
            watch_dir=self.cfg["watch_dir"],
            dest_root=self.cfg["dest_root"] or self.cfg["watch_dir"],
            rules=self.cfg.get("rules") or None,
            quiet_seconds=self.cfg["quiet_seconds"],
            interval=self.cfg["interval"],
            dry_run=self.cfg["dry_run"],
            db_path=self.db_path,
        )

        self.ui_queue: queue.Queue = queue.Queue()
        self.manual_queue: queue.Queue = queue.Queue()
        self.watcher_thread = WatcherThread(self.state, self.ui_queue, self.store)

        # Session counters shown in the dashboard header
        self.session_moved = 0
        self.session_errors = 0

        # Build UI
        self.root = tk.Tk()
        self.root.title("Download Watcher")
        self.root.geometry("960x680")
        self.root.minsize(760, 540)

        self._build_ui()
        self._load_initial_data()

        # Start watcher thread
        self.watcher_thread.start()

        # Poll UI queue
        self.root.after(100, self._poll_queue)

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        apply_theme(ttk.Style())

        # Main container with padding
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_dash = ttk.Frame(self.notebook, padding=10)
        self.tab_moves = ttk.Frame(self.notebook, padding=10)
        self.tab_activity = ttk.Frame(self.notebook, padding=10)
        self.tab_settings = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_dash, text="Dashboard")
        self.notebook.add(self.tab_moves, text="Recent Moves")
        self.notebook.add(self.tab_activity, text="Activity")
        self.notebook.add(self.tab_settings, text="Settings")

        self._build_dashboard()
        self._build_moves_tab()
        self._build_activity_tab()
        self._build_settings_tab()

        # ===== STATUS BAR =====
        self.statusbar_var = tk.StringVar(value="Ready")
        ttk.Label(self.root, textvariable=self.statusbar_var, relief=tk.SUNKEN, anchor=tk.W, padding=5).pack(
            fill=tk.X, side=tk.BOTTOM, padx=10, pady=(0, 10)
        )

    def _set_status(self, status: str):
        """Set status text + dot color (dot never carries meaning alone)."""
        self.status_var.set(status)
        dot, color = status_dot(status)
        self.dot_var.set(dot)
        self.dot_label.configure(foreground=color)

    def _build_dashboard(self):
        # ===== HEADER: Status Card + Token Display =====
        header = ttk.Frame(self.tab_dash)
        header.pack(fill=tk.X, pady=(0, 10))

        # Status Card
        status_frame = ttk.LabelFrame(header, text="Status", padding=10)
        status_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        top_row = ttk.Frame(status_frame)
        top_row.pack(fill=tk.X)

        self.dot_var = tk.StringVar(value="●")
        self.dot_label = ttk.Label(top_row, textvariable=self.dot_var, font=("Segoe UI", 14, "bold"))
        self.dot_label.pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Starting…")
        self.status_label = ttk.Label(
            top_row, textvariable=self.status_var, font=("Segoe UI", 14, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=(4, 0))
        self._set_status("Starting…")

        self.updated_var = tk.StringVar(value="")
        ttk.Label(top_row, textvariable=self.updated_var, foreground="gray").pack(
            side=tk.RIGHT
        )

        self.detail_var = tk.StringVar(value=summarize(self.session_moved, self.session_errors))
        ttk.Label(status_frame, textvariable=self.detail_var, foreground="gray").pack(
            anchor=tk.W
        )

        # Config Token Display
        token_frame = ttk.LabelFrame(header, text="Config", padding=10)
        token_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        self.token_text = tk.Text(
            token_frame,
            height=6,
            width=35,
            font=("Consolas", 9),
            state=tk.DISABLED,
            wrap=tk.NONE,
        )
        self.token_text.pack()
        self._update_token_display()

        # ===== CONTROLS =====
        controls = ttk.Frame(self.tab_dash)
        controls.pack(fill=tk.X, pady=(0, 10))

        self.btn_scan = ttk.Button(
            controls, text="Scan Now", command=self._on_scan_now, width=15
        )
        self.btn_scan.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_pause = ttk.Button(
            controls, text="Pause", command=self._on_pause_resume, width=15
        )
        self.btn_pause.pack(side=tk.LEFT, padx=5)

        self.btn_recover = ttk.Button(
            controls, text="Recover", command=self._on_recover, width=15
        )
        self.btn_recover.pack(side=tk.LEFT, padx=5)

        self.last_scan_var = tk.StringVar(value="")
        ttk.Label(controls, textvariable=self.last_scan_var, foreground="gray").pack(
            side=tk.RIGHT
        )

        # ===== STATS BAR CHART =====
        self.stats_frame = ttk.LabelFrame(self.tab_dash, text="Moves by Category", padding=10)
        self.stats_frame.pack(fill=tk.X, pady=(0, 10))

        self.stats_canvas = tk.Canvas(self.stats_frame, height=120, bg=PALETTE["SURFACE"], highlightthickness=1, highlightbackground=PALETTE["BORDER"])
        self.stats_canvas.pack(fill=tk.X)
        self.stats_canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_moves_tab(self):
        # ===== RECENT MOVES TABLE =====
        moves_frame = ttk.LabelFrame(self.tab_moves, text="Recent Moves", padding=10)
        moves_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("time", "category", "source", "destination", "size")
        self.tree = ttk.Treeview(moves_frame, columns=cols, show="headings", height=12)
        for col, width, anchor in [
            ("time", 140, tk.W),
            ("category", 100, tk.CENTER),
            ("source", 250, tk.W),
            ("destination", 250, tk.W),
            ("size", 80, tk.E),
        ]:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=width, anchor=anchor, stretch=(col in ("source", "destination")))

        vsb = ttk.Scrollbar(moves_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.tag_configure("even", background=PALETTE["SURFACE"], foreground=PALETTE["TEXT"])
        self.tree.tag_configure("odd", background=PALETTE["ROW_ALT"], foreground=PALETTE["TEXT"])
        self.tree.tag_configure("empty", foreground=PALETTE["MUTED"])
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_activity_tab(self):
        # Activity feed (wired in Task 5; shell only for now)
        feed_frame = ttk.LabelFrame(self.tab_activity, text="Activity", padding=10)
        feed_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("time", "event", "detail")
        self.activity_tree = ttk.Treeview(feed_frame, columns=cols, show="headings", height=12)
        for col, width, anchor in [
            ("time", 90, tk.W),
            ("event", 100, tk.CENTER),
            ("detail", 400, tk.W),
        ]:
            self.activity_tree.heading(col, text=col.title())
            self.activity_tree.column(col, width=width, anchor=anchor, stretch=(col == "detail"))

        vsb = ttk.Scrollbar(feed_frame, orient=tk.VERTICAL, command=self.activity_tree.yview)
        self.activity_tree.configure(yscrollcommand=vsb.set)
        self.activity_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_settings_tab(self):
        # Dry-run + DB folder live here (full settings content in Task 6)
        settings_row = ttk.Frame(self.tab_settings)
        settings_row.pack(fill=tk.X, pady=(0, 10))

        self.dry_var = tk.BooleanVar(value=self.state.dry_run)
        ttk.Checkbutton(settings_row, text="Dry run", variable=self.dry_var,
                        command=self._on_dry_toggle).pack(side=tk.LEFT, padx=5)

        self.btn_open_db = ttk.Button(
            settings_row, text="Open DB Folder", command=self._open_db_folder, width=15
        )
        self.btn_open_db.pack(side=tk.LEFT, padx=5)

    def _update_token_display(self):
        self.token_text.config(state=tk.NORMAL)
        self.token_text.delete("1.0", tk.END)
        lines = token_lines(self.state, self.db_path)
        self.token_text.insert("1.0", "\n".join(lines))
        self.token_text.config(state=tk.DISABLED)

    def _on_dry_toggle(self):
        self.state.dry_run = bool(self.dry_var.get())
        self.watcher_thread.watcher.dry_run = self.state.dry_run
        self._update_token_display()

    def _load_initial_data(self):
        self._refresh_stats()
        self._refresh_moves()

    def _refresh_stats(self):
        rows = self.store.stats_by_category()
        self._draw_stats_bars(rows)

    def _draw_stats_bars(self, rows: list[tuple[str, int]]):
        self.stats_canvas.delete("all")
        total = sum(n for _, n in rows)
        self.stats_frame.configure(text=f"Moves by Category — total {total}")
        if not rows:
            self.stats_canvas.create_text(
                10, 60, anchor=tk.W, text="No moves yet — run Scan Now or start watching", fill=PALETTE["MUTED"], font=("Segoe UI", 10)
            )
            return

        max_n = max(n for _, n in rows)
        w = self.stats_canvas.winfo_width() or 800
        h = self.stats_canvas.winfo_height() or 120
        padding = 40
        bar_h = 24
        gap = 8
        start_y = 20

        for i, (cat, n) in enumerate(rows[:8]):  # top 8 categories
            y = start_y + i * (bar_h + gap)
            bar_w = max(10, int((n / max_n) * (w - 2 * padding - 120)))
            # Bar
            self.stats_canvas.create_rectangle(
                padding, y, padding + bar_w, y + bar_h, fill=PALETTE["ACCENT"], outline=""
            )
            # Category label
            self.stats_canvas.create_text(
                padding - 10, y + bar_h // 2, anchor=tk.E, text=cat, fill=PALETTE["TEXT"], font=("Segoe UI", 9)
            )
            # Count
            self.stats_canvas.create_text(
                padding + bar_w + 8, y + bar_h // 2, anchor=tk.W, text=str(n), fill=PALETTE["TEXT"], font=("Segoe UI", 9, "bold")
            )

    def _on_canvas_resize(self, event):
        self._refresh_stats()

    def _refresh_moves(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        moves = self.store.recent_moves(limit=50)
        if not moves:
            self.tree.insert("", tk.END, values=("", "(no moves yet)", "", "", ""), tags=("empty",))
            return
        for i, m in enumerate(moves):
            ts = m["ts"]
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts_str = ts
            src = Path(m["src"]).name
            dst = Path(m["dst"]).name
            size = format_size(m["size"])
            dry = " (dry)" if m["dry_run"] else ""
            self.tree.insert("", tk.END, values=(ts_str, m["category"], src, dst + dry, size), tags=(stripe(i),))

    def _poll_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg[0] == "scan_result":
                    _, ok, moved = msg
                    if ok:
                        self.session_moved += moved
                        self._set_status("Watching")
                        self.last_scan_var.set(f"last scan: {moved} moved")
                        self.updated_var.set(f"Updated {datetime.now().strftime('%H:%M')}")
                        self.detail_var.set(summarize(self.session_moved, self.session_errors))
                        self.statusbar_var.set(f"Last scan moved {moved} file(s)")
                    else:
                        self.session_errors += 1
                        self._set_status("Error")
                        self.updated_var.set(f"Updated {datetime.now().strftime('%H:%M')}")
                        self.detail_var.set(summarize(self.session_moved, self.session_errors))
                        self.statusbar_var.set("Scan error")
                    self._refresh_stats()
                    self._refresh_moves()
        except queue.Empty:
            pass
        self.root.after(100, self._poll_queue)

    def _on_scan_now(self):
        self.statusbar_var.set("Manual scan running…")
        self.btn_scan.config(state=tk.DISABLED)

        def do_scan():
            report = scan_once(
                self.state.watch_dir,
                self.state.dest_root,
                rules=self.state.rules,
                quiet_seconds=self.state.quiet_seconds,
                dry_run=self.state.dry_run,
                store=self.store,
            )
            self.manual_queue.put(("manual_scan_done", report))

        threading.Thread(target=do_scan, daemon=True).start()

        def check_done():
            try:
                msg = self.manual_queue.get_nowait()
                if msg[0] == "manual_scan_done":
                    _, report = msg
                    self.btn_scan.config(state=tk.NORMAL)
                    self.session_moved += len(report.moved)
                    self._set_status("Watching" if not self.state.paused else "Paused")
                    self.last_scan_var.set(f"last scan: {len(report.moved)} moved")
                    self.updated_var.set(f"Updated {datetime.now().strftime('%H:%M')}")
                    self.detail_var.set(summarize(self.session_moved, self.session_errors))
                    self.statusbar_var.set(f"Manual scan: {len(report.moved)} moved")
                    self._refresh_stats()
                    self._refresh_moves()
                    return
            except queue.Empty:
                pass
            self.root.after(100, check_done)

        self.root.after(100, check_done)

    def _on_pause_resume(self):
        self.state.paused = not self.state.paused
        if self.state.paused:
            self.btn_pause.config(text="Resume")
            self._set_status("Paused")
            self.detail_var.set("Watcher paused - click Resume to continue")
            self.statusbar_var.set("Paused")
        else:
            self.btn_pause.config(text="Pause")
            self._set_status("Watching")
            self.detail_var.set(f"Watching {self.state.watch_dir} every {self.state.interval}s")
            self.statusbar_var.set("Resumed watching")

    def _on_recover(self):
        from .recovery import recover_pending

        self.statusbar_var.set("Recovering…")
        actions = recover_pending(self.store)
        msg = "\n".join(actions) if actions else "Journal clean; nothing to recover"
        self.statusbar_var.set("Recovery complete")
        # Show in a dialog
        tk.messagebox.showinfo("Recovery", msg)
        self._refresh_moves()

    def _open_db_folder(self):
        open_folder(self.db_path)

    def _on_close(self):
        self.state.running = False
        self.watcher_thread.join(timeout=2.0)
        self.store.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main(config_path: str | None = None):
    """Entry point for the GUI."""
    _hide_console()
    app = DwatcherGui(config_path)
    app.run()


if __name__ == "__main__":
    main()