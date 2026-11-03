"""BeaconHunt Launcher — a no-terminal GUI front door for the existing app.

Three steps for a non-technical user:
    1. Open this launcher (double-click the shortcut / .vbs / .exe)
    2. Pick a service
    3. Click Launch

It drives the existing BeaconHunt CLI in the background with the console hidden,
shows progress, and on success gives a clickable link + credentials. It does not
modify the existing app.
"""

from __future__ import annotations

import secrets
import threading
import webbrowser
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

import bh_backend as be


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = be.load_config()
        self.app_root = be.find_app_root(self.cfg.get("app_root") or None)
        self.running = False
        self.log_file: Path | None = None
        self.result: dict | None = None

        root.title("BeaconHunt Launcher")
        root.minsize(560, 420)
        try:
            ttk.Style().theme_use("clam")
        except tk.TclError:
            pass

        outer = ttk.Frame(root, padding=18)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        ttk.Label(outer, text="🛰  BeaconHunt", font=("", 17, "bold")).grid(
            row=0, column=0, sticky="w")
        ttk.Label(outer, text="Pick a service and click Launch. No terminal needed.",
                  foreground="#666").grid(row=1, column=0, sticky="w", pady=(0, 14))

        # --- service selection ----------------------------------------------
        sel = ttk.LabelFrame(outer, text="1 · Choose a service", padding=12)
        sel.grid(row=2, column=0, sticky="ew")
        sel.columnconfigure(0, weight=1)

        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._apply_filter())
        self.filter_entry = ttk.Entry(sel, textvariable=self.filter_var)
        self.filter_entry.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self._set_placeholder(self.filter_entry, "Filter services…")

        self.service_var = tk.StringVar()
        self.service_combo = ttk.Combobox(sel, textvariable=self.service_var,
                                          state="readonly", height=12)
        self.service_combo.grid(row=1, column=0, sticky="ew")

        # --- advanced (collapsed) -------------------------------------------
        self.adv_open = tk.BooleanVar(value=False)
        self.adv_btn = ttk.Button(outer, text="▸ Advanced", width=14,
                                  command=self._toggle_advanced)
        self.adv_btn.grid(row=3, column=0, sticky="w", pady=(10, 0))

        self.adv = ttk.Frame(outer, padding=(0, 6))
        self.adv.columnconfigure(1, weight=1)
        ttk.Label(self.adv, text="Findings (count)").grid(row=0, column=0, sticky="w", padx=4, pady=3)
        self.count = ttk.Spinbox(self.adv, from_=1, to=50, width=6)
        self.count.set(self.cfg.get("count", 5))
        self.count.grid(row=0, column=1, sticky="w", padx=4)
        ttk.Label(self.adv, text="Difficulty").grid(row=1, column=0, sticky="w", padx=4, pady=3)
        self.difficulty = ttk.Combobox(self.adv, width=10, state="readonly",
                                       values=["any", "easy", "medium", "hard"])
        self.difficulty.set(self.cfg.get("difficulty", "any"))
        self.difficulty.grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(self.adv, text="Web UI port").grid(row=2, column=0, sticky="w", padx=4, pady=3)
        self.port = ttk.Entry(self.adv, width=10)
        self.port.insert(0, str(self.cfg.get("web_port", 8800)))
        self.port.grid(row=2, column=1, sticky="w", padx=4)
        ttk.Label(self.adv, text="Web UI username").grid(row=3, column=0, sticky="w", padx=4, pady=3)
        self.user = ttk.Entry(self.adv, width=16)
        self.user.insert(0, self.cfg.get("web_user", "hunter"))
        self.user.grid(row=3, column=1, sticky="w", padx=4)

        # --- launch + progress ----------------------------------------------
        act = ttk.Frame(outer)
        act.grid(row=5, column=0, sticky="ew", pady=(14, 6))
        act.columnconfigure(1, weight=1)
        self.launch_btn = ttk.Button(act, text="🚀  Launch", command=self.on_launch)
        self.launch_btn.grid(row=0, column=0, sticky="w")
        self.status = ttk.Label(act, text="Ready.", foreground="#666")
        self.status.grid(row=0, column=1, sticky="w", padx=12)

        self.progress = ttk.Progressbar(outer, mode="indeterminate")
        self.detail = ttk.Label(outer, text="", foreground="#888", font=("", 9))

        # --- result / error panel -------------------------------------------
        self.panel = ttk.Frame(outer)
        self.panel.grid(row=8, column=0, sticky="ew", pady=(10, 0))
        self.panel.columnconfigure(0, weight=1)

        self._populate_services()
        if not self.app_root:
            self._show_error(
                "Couldn't find the BeaconHunt app.",
                "Place this launcher inside the BeaconHunt folder, or set the app "
                "folder under Advanced.", log=None)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- small helpers ---------------------------------------------------------

    def _set_placeholder(self, entry: ttk.Entry, text: str) -> None:
        entry.insert(0, text)
        entry.configure(foreground="#999")
        def on_in(_):
            if entry.get() == text:
                entry.delete(0, "end"); entry.configure(foreground="")
        def on_out(_):
            if not entry.get():
                entry.insert(0, text); entry.configure(foreground="#999")
        entry.bind("<FocusIn>", on_in)
        entry.bind("<FocusOut>", on_out)

    def _toggle_advanced(self) -> None:
        if self.adv_open.get():
            self.adv.grid_forget(); self.adv_btn.configure(text="▸ Advanced")
        else:
            self.adv.grid(row=4, column=0, sticky="ew"); self.adv_btn.configure(text="▾ Advanced")
        self.adv_open.set(not self.adv_open.get())

    def _populate_services(self) -> None:
        services = be.discover_services(self.app_root) if self.app_root else []
        self._all_values = [be.ALL_SERVICES] + services
        self.service_combo["values"] = self._all_values
        last = self.cfg.get("last_service", be.ALL_SERVICES)
        self.service_var.set(last if last in self._all_values else be.ALL_SERVICES)

    def _apply_filter(self) -> None:
        term = self.filter_var.get().strip().lower()
        if term in ("", "filter services…"):
            vals = self._all_values
        else:
            vals = [v for v in self._all_values if term in v.lower()]
        self.service_combo["values"] = vals
        if vals and self.service_var.get() not in vals:
            self.service_var.set(vals[0])

    def _set_status(self, text: str) -> None:
        self.root.after(0, lambda: self.status.configure(text=text))

    def _set_detail(self, text: str) -> None:
        self.root.after(0, lambda: self.detail.configure(text=text[:90]))

    def _clear_panel(self) -> None:
        for w in self.panel.winfo_children():
            w.destroy()

    # -- launch ---------------------------------------------------------------

    def on_launch(self) -> None:
        if self.running or not self.app_root:
            return
        service = self.service_var.get() or be.ALL_SERVICES
        try:
            count = int(self.count.get() or 5)
            port = int(self.port.get() or 8800)
        except ValueError:
            messagebox.showwarning("Check settings", "Count and port must be numbers.")
            return
        user = self.user.get().strip() or "hunter"
        difficulty = self.difficulty.get()
        password = secrets.token_urlsafe(9)

        # remember settings
        self.cfg.update({"last_service": service, "count": count,
                         "web_port": port, "web_user": user, "difficulty": difficulty})
        be.save_config(self.cfg)

        self.running = True
        self.launch_btn.configure(state="disabled")
        self._clear_panel()
        self.progress.grid(row=6, column=0, sticky="ew", pady=(8, 2))
        self.detail.grid(row=7, column=0, sticky="w")
        self.progress.start(12)
        self.log_file = be.new_log_path()

        args = (service, count, port, user, difficulty, password)
        threading.Thread(target=self._worker, args=args, daemon=True).start()

    def _log(self, line: str) -> None:
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
            except OSError:
                pass

    def _worker(self, service, count, port, user, difficulty, password) -> None:
        try:
            # 1) generate
            self._set_status("Creating scenario…")
            gen = ["generate", "--count", str(count)]
            if service != be.ALL_SERVICES:
                gen += ["--service", service]
            if difficulty and difficulty != "any":
                gen += ["--difficulty", difficulty]
            rc = be.run_cli_stream(self.app_root, gen, self._on_line)
            if rc != 0:
                return self._fail("generate")

            # 2) deploy (the slow one — build + plant)
            self._set_status("Starting the range… (first run builds images, may take a few minutes)")
            rc = be.run_cli_stream(self.app_root, ["deploy"], self._on_line)
            if rc != 0:
                return self._fail("deploy")

            # 3) web UI (detached, console-less)
            self._set_status("Starting the submission web UI…")
            be.start_web_detached(self.app_root, port, user, password, self.log_file)
            be.wait_for_port("127.0.0.1", port, timeout=20)

            self.result = {"url": f"http://127.0.0.1:{port}", "user": user,
                           "password": password, "service": service}
            self.root.after(0, self._success)
        except Exception as exc:  # never leave the UI stuck
            self._log(f"launcher error: {exc!r}")
            self.root.after(0, lambda: self._show_error(
                "Unexpected launcher error.", str(exc), log=self.log_file))
            self._finish()

    def _on_line(self, line: str) -> None:
        self._log(line)
        if line.strip():
            self._set_detail(line.strip())

    def _finish(self) -> None:
        self.running = False
        self.root.after(0, lambda: (
            self.progress.stop(), self.progress.grid_forget(),
            self.detail.grid_forget(), self.launch_btn.configure(state="normal")))

    def _fail(self, step: str) -> None:
        output = ""
        if self.log_file and self.log_file.exists():
            output = self.log_file.read_text(encoding="utf-8", errors="replace")
        msg = be.translate_error(step, output)
        self.root.after(0, lambda: self._show_error("Launch failed", msg, log=self.log_file))
        self._finish()

    # -- result / error UI ----------------------------------------------------

    def _success(self) -> None:
        self._finish()
        self._set_status("Running ✓")
        self._clear_panel()
        r = self.result
        box = ttk.LabelFrame(self.panel, text="✅  Instance is running", padding=12)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(0, weight=1)
        ttk.Label(box, text="Submission web UI:").grid(row=0, column=0, sticky="w")
        link = ttk.Label(box, text=r["url"], foreground="#1f6feb", cursor="hand2")
        link.grid(row=1, column=0, sticky="w")
        link.bind("<Button-1>", lambda _e: webbrowser.open(r["url"]))
        ttk.Label(box, text=f"Sign in:  {r['user']}  /  {r['password']}").grid(
            row=2, column=0, sticky="w", pady=(2, 8))
        hint = be.SERVICE_ACCESS.get(r["service"],
                                     "All services are up; see the web UI to start hunting.")
        ttk.Label(box, text=hint, foreground="#555", wraplength=460,
                  justify="left").grid(row=3, column=0, sticky="w", pady=(0, 8))
        bar = ttk.Frame(box); bar.grid(row=4, column=0, sticky="w")
        ttk.Button(bar, text="Open in Browser",
                   command=lambda: webbrowser.open(r["url"])).pack(side="left")
        ttk.Button(bar, text="Copy sign-in",
                   command=lambda: self._copy(f"{r['url']}  {r['user']} / {r['password']}")
                   ).pack(side="left", padx=8)

    def _show_error(self, title: str, message: str, log: Path | None) -> None:
        self._finish()
        self._set_status("Failed ✗")
        self._clear_panel()
        box = ttk.LabelFrame(self.panel, text=f"⚠  {title}", padding=12)
        box.grid(row=0, column=0, sticky="ew")
        box.columnconfigure(0, weight=1)
        ttk.Label(box, text=message, wraplength=480, justify="left").grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        if log:
            bar = ttk.Frame(box); bar.grid(row=1, column=0, sticky="w")
            ttk.Button(bar, text="View details",
                       command=lambda: self._open_log(log)).pack(side="left")
            ttk.Button(bar, text="Copy log",
                       command=lambda: self._copy_log(log)).pack(side="left", padx=8)

    def _copy(self, text: str) -> None:
        self.root.clipboard_clear(); self.root.clipboard_append(text)
        self._set_status("Copied to clipboard.")

    def _copy_log(self, log: Path) -> None:
        try:
            self._copy(log.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass

    def _open_log(self, log: Path) -> None:
        try:
            if be.IS_WINDOWS:
                import os
                os.startfile(str(log))  # noqa: S606
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(log)], **be._no_window_kwargs())
        except Exception:
            self._copy_log(log)

    def _on_close(self) -> None:
        if self.running:
            if not messagebox.askokcancel(
                    "Launch in progress",
                    "A launch is still running. Close anyway?\n\n"
                    "The range may keep building in the background."):
                return
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
