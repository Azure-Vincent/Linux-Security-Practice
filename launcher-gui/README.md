# BeaconHunt Launcher

A no-terminal, three-click front door for the existing **BeaconHunt** app. A
non-technical user can go from double-click → pick a service → **Launch** → a
running instance, without ever seeing PowerShell, Command Prompt, or any console.

This launcher is a **separate layer**. It does not modify, move, or import the
existing app — it drives it through the same command line a user would use
(`beaconhunt …`), with the console hidden. Everything here lives in this
`launcher-gui/` folder.

## What it does

1. **Open** the launcher (double-click the shortcut / `.vbs` / `.exe`).
2. **Choose a service** from a dropdown (populated automatically from the app's
   own catalog) — with a filter box.
3. **Launch** — it runs, in the background with no console:
   `beaconhunt generate` → `beaconhunt deploy` → `beaconhunt web`,
   shows a progress bar + status, then a success panel with the **web UI link**,
   **sign-in credentials**, the selected service's **access details**, and an
   **Open in Browser** button.

Failures become plain-language messages (e.g. "Docker Desktop isn't running…")
with **View details** / **Copy log** pointing at a full log file.

## Prerequisites

The launcher adds no new requirements beyond what the app itself needs:

- **Python 3.10+** with PyYAML (the app is a Python tool).
- **Docker Desktop**, running (the range runs in containers).

No admin rights required.

## Install & run

The launcher must sit **inside (or next to) the BeaconHunt app folder** so it
can find it. This folder already is. Then:

- **Double-click `BeaconHunt Launcher.vbs`** — opens the GUI with no console
  window (uses `pythonw`). This is the recommended, build-free way.
- To get a desktop shortcut: right-click `BeaconHunt Launcher.vbs` →
  *Send to* → *Desktop (create shortcut)*, then rename/icon it as you like.
- **Optional standalone `.exe`:** run `build_launcher_exe.bat` on Windows →
  produces `dist\BeaconHunt Launcher.exe` (windowless). Keep it in/next to the
  app folder. Note: the `.exe` still needs Python + Docker available, because it
  runs the app's own CLI (see *Limitations*).

First launch builds the container images and can take a few minutes; later
launches are fast.

## Where logs are stored

Per-launch logs (full stdout/stderr of the underlying commands) and the
launcher's own config live under:

- **Windows:** `%APPDATA%\BeaconHuntLauncher\` (logs in `logs\`)
- **macOS/Linux:** `~/.config/BeaconHuntLauncher/`

The error panel's **View details** opens the current log; **Copy log** copies it
for support.

## Adding new services

Automatic — the service list comes straight from the app's catalog. When the
app gains a new service folder under `catalog/<service>/`, it appears in the
dropdown next time you open the launcher. The only launcher-side extra is a
one-line human-readable "access details" hint in `bh_backend.py`
(`SERVICE_ACCESS`); without it the service still launches and the launcher shows
a generic "see the web UI" note.

## Configuration

The launcher keeps its **own** config (`config.json` in the folder above),
separate from the app's config. It remembers your last service, count, port,
username, and (optionally) the app folder path. Advanced settings (count,
difficulty, web port, username) are behind the **Advanced** toggle; the default
path is a true three-click launch.

## Limitations & assumptions

- **Python is still required.** The launcher runs the app's CLI, which is
  Python. Fully removing the Python prerequisite for end users would mean the
  **app** shipping a standalone CLI executable (e.g. `pyinstaller beaconhunt/cli.py`)
  — a change to the existing app's packaging, which this project intentionally
  does **not** make (read-only constraint). Documented here instead.
- **Docker is required and must be running** for `deploy`/`web`; the launcher
  detects the common "not running" case and says so in plain language.
- The launcher **selects one service** (or *All services*) and plants findings
  for it; `deploy` always brings the whole compose range up, so other service
  containers run too (unplanted). This mirrors how the app behaves.
- The web UI is started **detached** so it keeps running after you close the
  launcher; the containers run detached via `docker compose up -d` regardless.
  To stop everything, use the app's own `beaconhunt teardown`.
- **App discovery:** the launcher expects to be inside/next to the app folder
  (it looks for `beaconhunt/cli.py` or `docker-compose.yml`). If it can't find
  it, set the app folder under Advanced.
