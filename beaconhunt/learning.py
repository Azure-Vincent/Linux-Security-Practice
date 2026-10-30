"""Learning mode: per-finding explainers and service-by-service walkthroughs."""

from __future__ import annotations

from .catalog import Catalog
from .schema import Artifact

# Service-level hunt methodology taught in walkthrough mode. These are the
# general "where do I even start" commands a defender runs per service, before
# drilling into any specific finding.
SERVICE_METHODOLOGY: dict[str, list[str]] = {
    "ssh": [
        "grep -R . /root/.ssh /home/*/.ssh/authorized_keys 2>/dev/null   # rogue keys",
        "sshd -T | grep -Ei 'permitrootlogin|passwordauth|permitempty'   # effective config",
        "cat /etc/ssh/sshrc ~/.ssh/rc 2>/dev/null                        # sshrc hooks",
        "crontab -l; ls -la /etc/cron.*; systemctl list-timers --all     # persistence",
    ],
    "web": [
        "find /var/www -name '*.php' -newermt '-7 days'                  # recent files",
        "grep -RilE 'eval\\(|system\\(|passthru\\(|base64_decode' /var/www  # web shells",
        "find /var/www -name '.htaccess' -exec cat {} +                  # htaccess tricks",
        "ss -tlnp                                                         # listeners",
    ],
    "db": [
        "SELECT user, host FROM mysql.user;                              # rogue accounts",
        "SHOW GRANTS FOR ...;                                            # over-permissive",
        "SELECT * FROM information_schema.triggers;                      # trigger persistence",
    ],
    "smb": [
        "testparm -s                                                     # effective smb.conf",
        "smbclient -L //localhost -N                                     # anonymous shares",
        "grep -E 'guest ok|writable|read only' /etc/samba/smb.conf       # loose shares",
    ],
    "host": [
        "ss -tlnp                                                        # unexpected ports",
        "find / -perm -4000 -type f 2>/dev/null                          # suid binaries",
        "systemctl list-timers --all; systemctl list-units --type=service",
        "grep -vE '/nologin|/false' /etc/passwd | awk -F: '$3>=0'        # login shells",
    ],
}


def explain(art: Artifact) -> str:
    lines = [
        f"{art.name}  [{art.service}/{art.category} · {art.difficulty} · {art.points} pts]",
        "-" * 64,
        f"What it is:   {art.description}",
    ]
    if art.learn:
        lines.append(f"Technique:    {art.learn.strip()}")
    if art.hunt_commands:
        lines.append("How to find it:")
        for cmd in art.hunt_commands:
            lines.append(f"    $ {cmd}")
    if art.remediation:
        lines.append(f"How to fix it: {art.remediation.strip()}")
    return "\n".join(lines)


def walkthrough(catalog: Catalog, service: str | None = None) -> str:
    services = [service] if service else sorted(catalog.services)
    lines: list[str] = []
    for svc in services:
        lines.append("")
        lines.append(f"### Hunting {svc.upper()}")
        for cmd in SERVICE_METHODOLOGY.get(svc, []):
            lines.append(f"    $ {cmd}")
        lines.append("")
        lines.append(f"  Techniques planted in the {svc} catalog:")
        for art in sorted(catalog.filter(service=svc), key=lambda a: a.id):
            lines.append(f"    - {art.name} ({art.category}, {art.difficulty})")
    return "\n".join(lines)
