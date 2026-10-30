"""BeaconHunt launcher — a small desktop GUI that stands up a round.

Pick a seed and services, hit Launch, and BeaconHunt will:
  * generate the scenario,
  * build + start the range and plant the findings,
  * open a terminal already SSH'd in as the 'defender' admin,
  * start the submission web UI and open it in your browser.

Run it with `beaconhunt-gui`, `python -m beaconhunt.launcher`, the bundled
BeaconHunt.bat, or the built BeaconHunt.exe.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, scrolledtext

from .catalog import load_catalog
from .orchestrator import LaunchConfig, catalog_dir, run_launch, teardown


def _available_services() -> list[str]:
    try:
        svcs = sorted(load_catalog(catalog_dir()).services)
        return svcs or ["ssh"]
    except Exception:
        return ["ssh"]


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("BeaconHunt Launcher")
        root.minsize(620, 560)

        pad = {"padx": 8, "pady": 4}
        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="🛰  BeaconHunt", font=("", 16, "bold")).grid(
            row=0, column=0, columnspan=4, sticky="w")
        ttk.Label(frm, text="Contained blue-team training range — localhost only",
                  foreground="#888").grid(row=1, column=0, columnspan=4, sticky="w",
                                          pady=(0, 10))

        # --- scenario settings ------------------------------------------------
        box = ttk.LabelFrame(frm, text="Scenario", padding=10)
        box.grid(row=2, column=0, columnspan=4, sticky="ew")
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Seed (blank = random)").grid(row=0, column=0, sticky="w", **pad)
        self.seed = ttk.Entry(box, width=16)
        self.seed.grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(box, text="Findings (count)").grid(row=0, column=2, sticky="e", **pad)
        self.count = ttk.Spinbox(box, from_=1, to=50, width=6)
        self.count.set(5)
        self.count.grid(row=0, column=3, sticky="w", **pad)

        ttk.Label(box, text="Difficulty").grid(row=1, column=0, sticky="w", **pad)
        self.difficulty = ttk.Combobox(
            box, width=14, state="readonly",
            values=["any", "easy", "medium", "hard"])
        self.difficulty.set("any")
        self.difficulty.grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(box, text="Services").grid(row=2, column=0, sticky="nw", **pad)
        svc_frame = ttk.Frame(box)
        svc_frame.grid(row=2, column=1, columnspan=3, sticky="w", **pad)
        self.service_vars: dict[str, tk.BooleanVar] = {}
        for i, svc in enumerate(_available_services()):
            var = tk.BooleanVar(value=(svc == "ssh"))
            self.service_vars[svc] = var
            ttk.Checkbutton(svc_frame, text=svc, variable=var).grid(
                row=0, column=i, padx=6)

        # --- web UI settings --------------------------------------------------
        wbox = ttk.LabelFrame(frm, text="Submission web UI", padding=10)
        wbox.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        wbox.columnconfigure(1, weight=1)

        ttk.Label(wbox, text="Port").grid(row=0, column=0, sticky="w", **pad)
        self.port = ttk.Entry(wbox, width=10)
        self.port.insert(0, "8800")
        self.port.grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(wbox, text="Username").grid(row=0, column=2, sticky="e", **pad)
        self.user = ttk.Entry(wbox, width=14)
        self.user.insert(0, "hunter")
        self.user.grid(row=0, column=3, sticky="w", **pad)

        ttk.Label(wbox, text="Password (blank = random)").grid(
            row=1, column=0, sticky="w", **pad)
        self.password = ttk.Entry(wbox, width=20, show="•")
        self.password.grid(row=1, column=1, sticky="w", **pad)

        self.open_term = tk.BooleanVar(value=True)
        self.open_web = tk.BooleanVar(value=True)
        ttk.Checkbutton(wbox, text="Open SSH terminal", variable=self.open_term).grid(
            row=1, column=2, sticky="w", **pad)
        ttk.Checkbutton(wbox, text="Open browser", variable=self.open_web).grid(
            row=1, column=3, sticky="w", **pad)

        # --- actions ----------------------------------------------------------
        bar = ttk.Frame(frm)
        bar.grid(row=4, column=0, columnspan=4, sticky="ew", pady=10)
        self.launch_btn = ttk.Button(bar, text="🚀  Launch Range", command=self.on_launch)
        self.launch_btn.pack(side="left")
        self.teardown_btn = ttk.Button(bar, text="Tear down", command=self.on_teardown)
        self.teardown_btn.pack(side="left", padx=8)
        self.status = ttk.Label(bar, text="Idle.", foreground="#888")
        self.status.pack(side="left", padx=10)

        # --- log --------------------------------------------------------------
        self.log_widget = scrolledtext.ScrolledText(frm, height=16, wrap="word",
                                                     state="disabled", font=("Consolas", 9))
        self.log_widget.grid(row=5, column=0, columnspan=4, sticky="nsew")
        frm.rowconfigure(5, weight=1)
        frm.columnconfigure(0, weight=1)

        self.log("Ready. Make sure Docker Desktop is running, then Launch.")

    # -- helpers ---------------------------------------------------------------

    def log(self, msg: str) -> None:
        # Thread-safe append.
        self.root.after(0, self._append, str(msg))

    def _append(self, msg: str) -> None:
        self.log_widget.configure(state="normal")
        self.log_widget.insert("end", msg + "\n")
        self.log_widget.see("end")
        self.log_widget.configure(state="disabled")

    def _set_busy(self, busy: bool, status: str) -> None:
        self.root.after(0, lambda: (
            self.launch_btn.configure(state="disabled" if busy else "normal"),
            self.teardown_btn.configure(state="disabled" if busy else "normal"),
            self.status.configure(text=status),
        ))

    def _config(self) -> LaunchConfig:
        seed_txt = self.seed.get().strip()
        services = [s for s, v in self.service_vars.items() if v.get()] or ["ssh"]
        diff = self.difficulty.get()
        return LaunchConfig(
            seed=int(seed_txt) if seed_txt else None,
            count=int(self.count.get() or 5),
            services=services,
            difficulty=None if diff == "any" else diff,
            web_port=int(self.port.get() or 8800),
            web_user=self.user.get().strip() or "hunter",
            web_password=self.password.get(),
            open_terminal=self.open_term.get(),
            open_browser=self.open_web.get(),
        )

    # -- actions ---------------------------------------------------------------

    def on_launch(self) -> None:
        try:
            cfg = self._config()
        except ValueError as exc:
            self.log(f"Check your inputs: {exc}")
            return
        self._set_busy(True, "Launching…")

        def worker():
            run_launch(cfg, self.log)
            self._set_busy(False, "Running. Hunt + submit.")

        threading.Thread(target=worker, daemon=True).start()

    def on_teardown(self) -> None:
        self._set_busy(True, "Tearing down…")

        def worker():
            teardown(self.log)
            self._set_busy(False, "Torn down.")

        threading.Thread(target=worker, daemon=True).start()


def main() -> int:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("clam")
    except tk.TclError:
        pass
    App(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
