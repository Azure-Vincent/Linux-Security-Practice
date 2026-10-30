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
│   └── cli.py                  # the `beaconhunt` command
├── catalog/ssh/*.yaml          # planted-artifact definitions (the extensible catalog)
├── services/
│   ├── ssh/                    # hardened SSH target + declawed plant scripts
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

## Run a round

```bash
beaconhunt generate --seed 1337 --count 4 --service ssh   # pick findings (seedable)
beaconhunt deploy                                         # docker compose up + plant
```

Now hunt inside the range (SSH target is on `127.0.0.1:2222`), then submit:

```bash
beaconhunt submit --type backdoor  --service ssh \
    --evidence "/root/.ssh/authorized_keys line 3"
beaconhunt submit --type misconfig --service ssh \
    --evidence "PermitRootLogin yes in /etc/ssh/sshd_config.d/99-beaconhunt.conf"

beaconhunt hint  --service ssh     # stuck? a tiered hint (costs points)
beaconhunt grade                   # score + report + record to the scoreboard
```

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

SSH is implemented end-to-end as a vertical slice (plant → hunt → grade →
report → scoreboard → learn). Web / DB / SMB / host-level catalogs follow the
same pattern and are the next services to fill in.
