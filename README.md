# BeaconHunt

A **contained, defensive-security training range** for blue-team / CCDC
practice. BeaconHunt stands up a deliberately-vulnerable environment in
containers it manages itself, plants a *randomized, seedable* set of
compromises and misconfigurations, and then acts as a grader: you hunt through
the running system, submit what you find, and BeaconHunt scores your accuracy,
completeness, and speed — then shows you what you missed and how a defender
would fix it.

Think "CTF generator + answer key + scoreboard" for system hardening.

> ### ⚠️ Scope & intent — read this
> BeaconHunt is for **authorized, defensive training on systems you own**.
> * It runs **only** against `localhost` and the containers it spins up itself.
>   Every network-touching command passes through `beaconhunt.safety`, which
>   **refuses any external host**.
> * The `sink` container sits on an `internal: true` network with **no route to
>   the internet**, and planted "beacons" are hardcoded to call the `sink`
>   service name — so a beacon can only ever hit the bundled local sink, never a
>   real host. Service ports are published on `127.0.0.1` only, so the range is
>   reachable from your loopback but not from the LAN.
> * Planted artifacts are **declawed training stubs**: realistic enough to hunt
>   by signature, but neutered so they are not functioning weapons (e.g. the
>   `sshrc` "backdoor" only writes a log marker; the rogue key's private half is
>   discarded at plant time).
>
> Do not point it at anything else, and do not use the planting techniques
> outside this training sandbox.

---

## Layout

```
beaconhunt/
├── docker-compose.yml          # the range (internal net, loopback-only ports)
├── beaconhunt/                 # the Python engine + CLI
│   ├── safety.py               # localhost/managed-container scope guard (chokepoint)
│   ├── schema.py               # declarative artifact schema + validation
│   ├── catalog.py              # loads the YAML catalog
│   ├── scenario.py             # seedable scenario generator
│   ├── grader.py               # fuzzy/path-normalized grading vs. the answer key
│   ├── session.py              # per-round state (submissions, hints, timing)
│   ├── scoreboard.py           # persistent history across rounds
│   ├── report.py               # end-of-round report
│   ├── learning.py             # explainers + service-by-service walkthrough
│   ├── hints.py                # shared tiered-hint logic (CLI + web UI)
│   ├── webui.py                # local submission web UI (127.0.0.1, stdlib only)
│   ├── orchestrator.py         # headless launch sequence (generate→deploy→ssh→web)
│   ├── launcher.py             # Tkinter launcher GUI
│   └── cli.py                  # the `beaconhunt` command
├── beaconhunt_gui.py           # launcher entry point (what the .exe is built from)
├── BeaconHunt.bat              # double-click launcher (needs Python)
├── build_windows_exe.bat       # builds dist\BeaconHunt.exe (run on Windows)
├── catalog/ssh/*.yaml          # planted-artifact definitions (the extensible catalog)
├── catalog/web/*.yaml          # web-server findings
├── catalog/db/*.yaml           # database findings
├── catalog/smb/*.yaml          # Samba/SMB findings
├── catalog/mail/*.yaml         # mail-server findings
├── catalog/ftp/*.yaml          # FTP findings
├── catalog/dns/*.yaml          # DNS findings
├── catalog/redis/*.yaml        # Redis findings
├── catalog/host/*.yaml         # host-level findings (passwd/sudoers/systemd/…)
├── services/
│   ├── ssh/                    # hardened SSH target + declawed plant scripts
│   ├── web/                    # hardened Apache+PHP target + declawed plant scripts
│   ├── db/                     # hardened MariaDB target + declawed SQL plant scripts
│   ├── smb/                    # hardened Samba target + declawed plant scripts
│   ├── mail/                   # hardened Postfix+Dovecot target + declawed plant scripts
│   ├── ftp/                    # hardened vsftpd target + declawed plant scripts
│   ├── dns/                    # hardened BIND9 target + declawed plant scripts
│   ├── redis/                  # hardened Redis target + declawed plant scripts
│   ├── host/                   # generic Linux host + declawed host-level plant scripts
│   └── sink/                   # local beacon sink (stands in for C2)
├── state/                      # scenarios, round state, scoreboard (git-ignored)
└── tests/                      # offline engine tests (no Docker needed)
```

## Planted-artifact schema

Every finding is declared in YAML so the catalog is easy to extend — drop a new
`.yaml` under `catalog/<service>/` and it is picked up automatically. Full field
reference lives in `beaconhunt/schema.py`; the shape is:

```yaml
id: ssh-authorized-keys-backdoor      # unique slug
name: "Rogue key in root's authorized_keys"
service: ssh                          # ssh | web | db | smb | host
category: backdoor                    # backdoor|beacon|persistence|misconfig|weak-cred|privesc
difficulty: easy                      # easy | medium | hard
points: 100
description: "one-line summary of the planted condition"

install:
  script: plant/authorized_keys_backdoor.sh   # declawed planter, run in-container

detection:                            # the ANSWER KEY
  signatures:                         # machine checks that verify the plant is live
    - type: file_line                 # file_line|file_exists|process|port|user|config|cron|timer
      path: /root/.ssh/authorized_keys
      match: "beaconhunt-trainingkey" # substring (set `regex: true` for a pattern)
  accept_evidence:                    # what a user submission must look like to score
    paths:    ["/root/.ssh/authorized_keys"]
    keywords: ["authorized_keys", "ssh-ed25519"]
    require:  any                     # path | keyword | any

remediation:   "how a defender fixes it"
hunt_commands: ["cat /root/.ssh/authorized_keys", "..."]
learn:         "longer explainer of the technique"
```

## Install

```bash
pip install -e .          # installs the `beaconhunt` console command + PyYAML
```

You can also run it without installing, as `python3 -m beaconhunt.cli …`.
Standing up the live range additionally needs **Docker** with the Compose
plugin. All scenario/grading/learning commands work offline without Docker.

## Quick start — the launcher (GUI / executable)

The easiest way to run everything is the desktop launcher. You pick a seed and
services, click **Launch**, and BeaconHunt will: generate the scenario → build
and start the range + plant the findings → open a terminal **already SSH'd in
as `defender`** → start the submission web UI and open it in your browser.

**Requirements:** Docker Desktop installed and running. (Python 3.10+ if you
run the `.bat`; the built `.exe` is standalone but still drives Docker Desktop.)

Three ways to launch it, pick one:

```text
1. Double-click  BeaconHunt.bat            (needs Python installed)
2. beaconhunt-gui                          (after `pip install -e .`)
3. Build a standalone exe, then run it:
       build_windows_exe.bat   ->   dist\BeaconHunt.exe   (double-click)
```

> The prebuilt `.exe` has to be produced **on Windows** (PyInstaller can't
> cross-compile), which is exactly what `build_windows_exe.bat` does — it
> bundles the catalog, services, and compose file into one `dist\BeaconHunt.exe`.

The launcher window:

```text
 🛰  BeaconHunt Launcher
 ┌─ Scenario ──────────────────────────────────────────────┐
 │ Seed (blank = random) [____]   Findings (count) [ 5 ]    │
 │ Difficulty [ any ▾ ]                                     │
 │ Services   ☑ ssh  ☐ web  ☐ db  ☐ smb  ☐ host            │
 └──────────────────────────────────────────────────────────┘
 ┌─ Submission web UI ─────────────────────────────────────┐
 │ Port [8800]   Username [hunter]                          │
 │ Password (blank = random) [••••]  ☑ Open SSH terminal    │
 │                                   ☑ Open browser         │
 └──────────────────────────────────────────────────────────┘
   [ 🚀 Launch Range ]  [ Tear down ]   Idle.
 ┌─ log ───────────────────────────────────────────────────┐
 │ Scenario seed=1337: 4 finding(s), 430 pts.               │
 │ $ docker compose ... up -d --build                       │
 │ sshd is up.  Opening terminal: ssh defender@127.0.0.1 …  │
 │ Web UI on http://127.0.0.1:8800 (user: hunter · …)       │
 └──────────────────────────────────────────────────────────┘
```

Everything the launcher does is also available as the individual CLI commands
below.

## Run a round (CLI)

```bash
beaconhunt generate --seed 1337 --count 4 --service ssh   # pick findings (seedable)
beaconhunt deploy                                         # docker compose up + plant
```

### Getting into the box to hunt

There are two ways in, by design:

| Access | How | Who it models |
|--------|-----|----------------|
| **Defender / admin** | `ssh defender@127.0.0.1 -p 2222` (password `defender`), then `sudo …` — or `docker compose -p beaconhunt exec ssh bash` for a direct root shell | **You**, the blue-teamer with admin on your own box. Use this to inspect and **remediate**. |
| **Attacker foothold** | `ssh svc-backup@127.0.0.1 -p 2222` (password `Summer2024`) | A low-priv account an intruder landed — it *is* one of the findings. Unprivileged on purpose; it can't read `/root` or `sudo`. |

So to fix root-owned findings (e.g. the `authorized_keys` backdoor), log in as
`defender` and `sudo`, or exec in as root:

```bash
ssh defender@127.0.0.1 -p 2222            # password: defender
sudo cat /root/.ssh/authorized_keys
sudo sed -i '/beaconhunt-trainingkey/d' /root/.ssh/authorized_keys
```

The `defender` account is part of the base image — it is **not** a planted
finding and is never graded. Change its password at build time with
`--build-arg DEFENDER_PASSWORD=…`.

> **"REMOTE HOST IDENTIFICATION HAS CHANGED" on reconnect?** Each rebuild
> regenerates the container's SSH host keys, so `[127.0.0.1]:2222` gets a new
> fingerprint and clashes with your saved `known_hosts`. Clear the stale entry:
> ```bash
> ssh-keygen -R "[127.0.0.1]:2222"
> ```
> The launcher's auto-opened terminal already skips `known_hosts` for this
> disposable localhost target, so it never hits this. To do the same manually:
> ```bash
> ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
>     defender@127.0.0.1 -p 2222     # use NUL instead of /dev/null on Windows
> ```

Now hunt inside the range, then submit:

```bash
beaconhunt submit --type backdoor  --service ssh \
    --evidence "/root/.ssh/authorized_keys line 3"
beaconhunt submit --type misconfig --service ssh \
    --evidence "PermitRootLogin yes in /etc/ssh/sshd_config.d/99-beaconhunt.conf"

beaconhunt hint  --service ssh     # stuck? a tiered hint (costs points)
beaconhunt grade                   # score + report + record to the scoreboard
```

### Submission web UI

Prefer a browser? Launch the local submission GUI (stdlib only, no extra
dependencies). It drives the same engine and state as the CLI:

```bash
beaconhunt web            # serves http://127.0.0.1:8800
beaconhunt web --port 9000
```

It is bound to `127.0.0.1` only (localhost scope), so it is never reachable
from the LAN. From the page you can generate a round, submit findings, take
hints, grade, and watch the scoreboard — and submissions you make in the CLI
and the UI share the same round state.

#### Signing in

The web UI requires a login (random session cookie, `HttpOnly` + `SameSite`,
constant-time password check). You never commit a password — supply one or let
BeaconHunt generate it:

```bash
beaconhunt web                                   # random password, printed at startup
beaconhunt web --user vincent --password hunt42  # pick your own
BEACONHUNT_WEB_PASSWORD=hunt42 beaconhunt web    # or via env var
beaconhunt web --no-auth                         # disable login (localhost only)
```

| Field    | Value |
|----------|-------|
| Address  | `http://127.0.0.1:8800` (loopback only — change the port with `--port`) |
| Username | `hunter` by default, or whatever you pass to `--user` |
| Password | what you pass to `--password` / `$BEACONHUNT_WEB_PASSWORD`, else a random one **printed in the terminal** when the server starts |

The server prints the exact address, username, and password on startup:

```
========================================================
  BeaconHunt web UI   http://127.0.0.1:8800
  Address : 127.0.0.1  (localhost only — not on the LAN)
  Username: hunter
  Password: q51XMH3i1cgl   (generated for this run)
========================================================
```

Open that URL, sign in, and use the **sign out** link (top-right) when done.
Sessions are in-memory, so restarting the server signs everyone out.

Example report (abridged):

```
  Score:           205 / 430
  True positives:  3     False positives: 1 (-15)     Missed: 1
  Detection rate by category:  backdoor 1/1 · misconfig 1/1 · weak-cred 0/1
  MISSED FINDINGS (what was there and how to fix it):
    • Service account with weak password  [ssh/weak-cred, 120 pts]
        Where:  /etc/passwd
        Fix:    Disable or remove the account (usermod -L / userdel) ...
```

## Learn

```bash
beaconhunt learn --service ssh                    # hunt methodology + what's planted
beaconhunt learn ssh-authorized-keys-backdoor     # deep-dive one technique
beaconhunt reveal                                 # full answer key (give-up / study)
beaconhunt scoreboard                             # track improvement across rounds
```

## Reset / teardown

```bash
beaconhunt reset       # docker compose down -v, then redeploy the same scenario fresh
beaconhunt teardown    # docker compose down -v (tear the range down completely)
```

Deploy/reset/teardown are idempotent; `teardown` removes containers and volumes
so the next `deploy` rebuilds a clean range.

## Tests

```bash
python3 -m pytest        # 18 offline tests: schema, safety, seeding, grading, report
```

## Extending

* **New finding on an existing service:** add a YAML file under
  `catalog/<service>/`, write a declawed `plant/*.sh` that produces its
  signature, and register it in that service's `plant-dispatch.sh`.
* **New service:** add `services/<svc>/` (Dockerfile + plant scripts +
  dispatcher), a compose entry (loopback-only ports, on the `range` network),
  and a `catalog/<svc>/` directory. The generator, grader, report, and
  scoreboard pick it up with no code changes.

### Status

Nine services are implemented end-to-end (plant → hunt → grade → report →
scoreboard → learn): SSH, the web server (Apache+PHP), the database (MariaDB),
SMB (Samba), mail (Postfix+Dovecot), FTP (vsftpd), DNS (BIND9), Redis, and a
generic Linux host for host-level artifacts — **45 findings across all six
categories**.

Targets and how to hunt them:

| Service | Port | Get in to hunt / remediate |
|---------|------|-----------------------------|
| ssh  | `127.0.0.1:2222` | `ssh defender@127.0.0.1 -p 2222` (sudo), or `docker compose -p beaconhunt exec ssh bash` |
| web  | `127.0.0.1:8080` | browser, or `docker compose -p beaconhunt exec web bash` (root) |
| db   | `127.0.0.1:3306` | `docker compose -p beaconhunt exec db mariadb -uroot -pbeaconhunt-root` |
| smb  | `127.0.0.1:445`  | `docker compose -p beaconhunt exec smb bash` (root); `testparm -s`, `smbclient -L //127.0.0.1 -N`, `pdbedit -L` |
| mail | `127.0.0.1:2525` (SMTP), `127.0.0.1:1143` (IMAP) | `docker compose -p beaconhunt exec mail bash` (root); `postconf -n`, `cat /etc/aliases`, `ls -la /home/*/.forward` |
| ftp  | `127.0.0.1:2121` | `docker compose -p beaconhunt exec ftp bash` (root); `grep -nE 'anon|chroot|write' /etc/vsftpd.conf`, `ls -la /srv/ftp` |
| dns  | `127.0.0.1:5353` (udp/tcp) | `docker compose -p beaconhunt exec dns bash` (root); `named-checkconf -p`, `cat /etc/bind/db.acme.local`, `dig @127.0.0.1 -p 5353 acme.local AXFR` |
| redis | `127.0.0.1:6379` | `docker compose -p beaconhunt exec redis bash` (root); `grep -nE 'bind|protected-mode|requirepass' /etc/redis/redis.conf`, `redis-cli -a beaconhunt-redis --no-auth-warning --scan` |
| host | `127.0.0.1:2200` | `ssh defender@127.0.0.1 -p 2200` (sudo), or `docker compose -p beaconhunt exec host bash` |

Host-level hunting: `awk -F: '($3==0)' /etc/passwd` (UID-0 accounts),
`cat /etc/sudoers.d/*`, `ls -la /etc/systemd/system/*.timer`, `ss -tlnp`
(unexpected listeners), `grep -R HISTFILE /etc/profile.d`.

The DB findings are hunted with SQL — e.g. `SELECT User,Host FROM mysql.user;`,
`SHOW GRANTS FOR 'webapp'@'%';`, `SELECT trigger_name, action_statement FROM
information_schema.triggers;`. Submit the user/grant/trigger as your evidence
(e.g. `--service db --type backdoor --evidence "rogue user dbsupport"`).
