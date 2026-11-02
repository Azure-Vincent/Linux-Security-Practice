"""BeaconHunt Launcher — backend (no GUI).

This module is the *separate layer* that drives the existing BeaconHunt app
purely through its command-line interface, exactly as a user would. It never
imports the app's Python modules or edits any of its files.

Everything here is GUI-free so it can be tested headlessly; the Tkinter UI in
beaconhunt_launcher.py sits on top of it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

IS_WINDOWS = os.name == "nt"
APP_NAME = "BeaconHuntLauncher"

# How the launcher describes where to go once a service is running. This is the
# launcher's OWN knowledge (not read from the app), kept here deliberately.
SERVICE_ACCESS = {
    "ssh":  "SSH target on 127.0.0.1:2222 — ssh defender@127.0.0.1 -p 2222 (password: defender)",
    "web":  "Web app at http://127.0.0.1:8080",
    "db":   "MariaDB on 127.0.0.1:3306 — admin: root / beaconhunt-root",
    "smb":  "Samba on 127.0.0.1:445",
    "mail": "Mail on 127.0.0.1:2525 (SMTP) and 127.0.0.1:1143 (IMAP)",
    "ftp":  "FTP on 127.0.0.1:2121",
    "dns":  "DNS on 127.0.0.1:5353 (udp/tcp)",
    "redis": "Redis on 127.0.0.1:6379 — password: beaconhunt-redis",
    "host": "Host box on 127.0.0.1:2200 — ssh defender@127.0.0.1 -p 2200 (password: defender)",
}

ALL_SERVICES = "All services"


# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #

def _here() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def find_app_root(override: str | None = None) -> Path | None:
    """Locate the existing BeaconHunt app (the folder holding the package)."""
    candidates = []
    if override:
        candidates.append(Path(override))
    here = _here()
    candidates += [here.parent, here, Path.cwd()]
    for c in candidates:
        try:
            c = c.resolve()
        except OSError:
            continue
        if (c / "beaconhunt" / "cli.py").exists() or (c / "docker-compose.yml").exists():
            return c
    return None


def config_dir() -> Path:
    if IS_WINDOWS:
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    d = base / APP_NAME
    (d / "logs").mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return config_dir() / "config.json"


def new_log_path() -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return config_dir() / "logs" / f"launch-{stamp}.log"


# --------------------------------------------------------------------------- #
# config (the launcher's own, separate from the app's)
# --------------------------------------------------------------------------- #

DEFAULT_CONFIG = {
    "last_service": ALL_SERVICES,
    "count": 5,
    "web_port": 8800,
    "web_user": "hunter",
    "difficulty": "any",
    "app_root": "",
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    try:
        cfg.update(json.loads(config_path().read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg: dict) -> None:
    try:
        config_path().write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except OSError:
        pass


# --------------------------------------------------------------------------- #
# running the app's CLI with the console hidden
# --------------------------------------------------------------------------- #

def _python_cmd() -> list[str]:
    """A command prefix that can run `-m beaconhunt.cli`."""
    if not getattr(sys, "frozen", False):
        return [sys.executable]
    # Frozen launcher: find a system Python to run the app (the app needs one).
    for cand in ("py", "python", "python3"):
        exe = shutil.which(cand)
        if exe:
            return [exe, "-3"] if cand == "py" else [exe]
    return ["python"]


def _no_window_kwargs() -> dict:
    """subprocess kwargs that keep any console window hidden."""
    kw: dict = {}
    if IS_WINDOWS:
        kw["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
        kw["startupinfo"] = si
    return kw


def _env(app_root: Path) -> dict:
    env = dict(os.environ)
    # Make `-m beaconhunt.cli` importable without requiring a pip install.
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(app_root) + (os.pathsep + existing if existing else "")
    return env


@dataclass
class CliResult:
    returncode: int
    output: str


def run_cli(app_root: Path, args: list[str], timeout: float = 120) -> CliResult:
    cmd = _python_cmd() + ["-m", "beaconhunt.cli", *args]
    try:
        res = subprocess.run(
            cmd, cwd=str(app_root), env=_env(app_root),
            capture_output=True, text=True, timeout=timeout, **_no_window_kwargs(),
        )
    except FileNotFoundError:
        return CliResult(127, "Python interpreter not found.")
    except subprocess.TimeoutExpired:
        return CliResult(124, "The command timed out.")
    return CliResult(res.returncode, (res.stdout or "") + (res.stderr or ""))


def run_cli_stream(app_root: Path, args: list[str], on_line) -> int:
    """Run a CLI subcommand, streaming each output line to `on_line`."""
    cmd = _python_cmd() + ["-m", "beaconhunt.cli", *args]
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(app_root), env=_env(app_root),
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
            **_no_window_kwargs(),
        )
    except FileNotFoundError:
        on_line("Python interpreter not found.")
        return 127
    assert proc.stdout is not None
    for line in proc.stdout:
        on_line(line.rstrip())
    return proc.wait()


# --------------------------------------------------------------------------- #
# service discovery (same source the app uses, read via the CLI)
# --------------------------------------------------------------------------- #

_SERVICE_RE = re.compile(r"^\s+([a-z0-9_-]+)/[a-z0-9_-]+\b")


def discover_services(app_root: Path) -> list[str]:
    """List services by parsing `beaconhunt catalog`; fall back to the dirs."""
    res = run_cli(app_root, ["catalog"], timeout=60)
    found: set[str] = set()
    if res.returncode == 0:
        for line in res.output.splitlines():
            m = _SERVICE_RE.match(line)
            if m:
                found.add(m.group(1))
    if not found:
        cat = app_root / "catalog"
        if cat.is_dir():
            found = {p.name for p in cat.iterdir() if p.is_dir()}
    return sorted(found)


# --------------------------------------------------------------------------- #
# launching the range
# --------------------------------------------------------------------------- #

def start_web_detached(app_root: Path, port: int, user: str, password: str,
                       log_file: Path) -> int | None:
    """Start `beaconhunt web` as a detached, console-less background process."""
    cmd = _python_cmd() + ["-m", "beaconhunt.cli", "web",
                           "--port", str(port), "--user", user]
    env = _env(app_root)
    env["BEACONHUNT_WEB_PASSWORD"] = password
    kw = _no_window_kwargs()
    if IS_WINDOWS:
        kw["creationflags"] = kw.get("creationflags", 0) | 0x00000008  # DETACHED_PROCESS
    else:
        kw["start_new_session"] = True
    try:
        fh = open(log_file, "a", encoding="utf-8")
        proc = subprocess.Popen(cmd, cwd=str(app_root), env=env,
                                stdout=fh, stderr=subprocess.STDOUT, **kw)
        return proc.pid
    except OSError:
        return None


def wait_for_port(host: str, port: int, timeout: float = 20.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except OSError:
            time.sleep(0.5)
    return False


# --------------------------------------------------------------------------- #
# plain-language error translation
# --------------------------------------------------------------------------- #

def translate_error(step: str, output: str) -> str:
    low = output.lower()
    if ("docker" in low and ("daemon" in low or "pipe" in low
                             or "cannot connect" in low or "connect:" in low)) \
            or "dockerdesktoplinuxengine" in low:
        return ("Docker Desktop isn't running (or isn't installed). Open Docker "
                "Desktop, wait until it says “Engine running”, then try again.")
    if "no space left" in low:
        return ("The machine is out of disk space. Free some space (or run "
                "“Tear down”) and try again.")
    if "python interpreter not found" in low or "no module named" in low:
        return ("Python 3.10+ is required and wasn't found. Install it from "
                "python.org, then try again.")
    if step == "generate":
        return "Couldn't create the scenario. See details for the full output."
    if step == "deploy":
        return ("Couldn't start the range. This is usually Docker not running. "
                "See details for the full output.")
    return "Something went wrong. See details for the full output."
