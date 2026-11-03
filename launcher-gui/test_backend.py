"""Headless tests for the launcher backend (no GUI, no Docker)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bh_backend as be  # noqa: E402

APP_ROOT = HERE.parent  # launcher-gui/ lives inside the app


def test_find_app_root():
    root = be.find_app_root()
    assert root is not None
    assert (root / "beaconhunt" / "cli.py").exists()


def test_discover_services_matches_catalog_dirs():
    root = be.find_app_root()
    services = be.discover_services(root)
    on_disk = sorted(p.name for p in (root / "catalog").iterdir() if p.is_dir())
    # Every catalog directory shows up as a selectable service.
    assert set(on_disk) <= set(services)
    assert "ssh" in services and "redis" in services


def test_run_cli_drives_the_app():
    root = be.find_app_root()
    res = be.run_cli(root, ["--version"])
    assert res.returncode == 0
    assert "beaconhunt" in res.output.lower()


def test_translate_error_docker():
    msg = be.translate_error(
        "deploy",
        "failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine")
    assert "Docker Desktop" in msg


def test_translate_error_disk():
    assert "disk space" in be.translate_error("deploy", "write error: no space left on device")


def test_config_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("APPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    cfg = be.load_config()
    cfg["last_service"] = "redis"
    be.save_config(cfg)
    assert be.load_config()["last_service"] == "redis"


def test_service_access_covers_all_services():
    root = be.find_app_root()
    for svc in be.discover_services(root):
        assert svc in be.SERVICE_ACCESS, f"no access hint for {svc}"


def test_linux_launcher_scripts_are_valid():
    import subprocess
    for name in ("run-launcher.sh", "install-linux.sh"):
        p = HERE / name
        assert p.exists() and os.access(p, os.X_OK), f"{name} missing or not executable"
        rc = subprocess.run(["bash", "-n", str(p)]).returncode
        assert rc == 0, f"{name} has a syntax error"


def test_desktop_entry_is_no_terminal():
    tmpl = (HERE / "beaconhunt-launcher.desktop.template").read_text()
    assert "Terminal=false" in tmpl
    assert "Exec=" in tmpl
