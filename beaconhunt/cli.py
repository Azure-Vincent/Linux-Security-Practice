"""BeaconHunt command-line interface.

Round lifecycle:
    beaconhunt generate --seed 1337 --count 5 --service ssh
    beaconhunt deploy                 # docker compose up + plant selected artifacts
    beaconhunt submit --type backdoor --service ssh \
        --evidence "/root/.ssh/authorized_keys line 3"
    beaconhunt hint  --service ssh    # costs points
    beaconhunt grade                  # score + report + record to scoreboard
    beaconhunt reveal                 # answer key (learning)
    beaconhunt teardown               # tear the range down
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from . import __version__, learning, report, safety, scoreboard
from .catalog import DEFAULT_CATALOG_DIR, load_catalog
from .grader import Submission, grade
from .hints import choose_hint
from .scenario import (
    STATE_DIR,
    current_seed,
    generate_scenario,
    load_scenario,
)
from .session import load_round, save_round

REPO_ROOT = Path(__file__).resolve().parent.parent
COMPOSE_FILE = REPO_ROOT / "docker-compose.yml"


def _resolve_seed(args) -> int:
    seed = getattr(args, "seed", None)
    if seed is None:
        seed = current_seed(args.state_dir)
    if seed is None:
        sys.exit("No active scenario. Run `beaconhunt generate` first.")
    return seed


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #

def cmd_catalog(args) -> int:
    cat = load_catalog(args.catalog)
    rows = cat.filter(service=args.service, category=args.category,
                      difficulty=args.difficulty)
    print(f"{len(rows)} artifact(s) in catalog {args.catalog}:\n")
    for art in sorted(rows, key=lambda a: (a.service, a.category, a.id)):
        print(f"  {art.id}")
        print(f"      {art.service}/{art.category} · {art.difficulty} · "
              f"{art.points} pts — {art.name}")
    return 0


def cmd_generate(args) -> int:
    cat = load_catalog(args.catalog)
    scenario = generate_scenario(
        cat,
        seed=args.seed,
        count=args.count,
        services=[args.service] if args.service else None,
        categories=[args.category] if args.category else None,
        difficulties=[args.difficulty] if args.difficulty else None,
    )
    scenario.save(args.state_dir)
    # Fresh round for this seed.
    save_round(load_round(scenario.seed, args.state_dir), args.state_dir)
    print(f"Generated scenario seed={scenario.seed} with "
          f"{len(scenario.findings)} finding(s), {scenario.total_points} pts total.")
    print("Share this seed to reproduce the exact range.\n")
    for f in scenario.findings:
        print(f"  (hidden) {f.service}/{f.category} · {f.difficulty} · {f.points} pts")
    print("\nNext: `beaconhunt deploy` to stand up the range and plant findings.")
    return 0


def _compose(*cmd: str) -> int:
    if not COMPOSE_FILE.exists():
        print(f"compose file not found: {COMPOSE_FILE}", file=sys.stderr)
        return 1
    full = ["docker", "compose", "-p", safety.COMPOSE_PROJECT,
            "-f", str(COMPOSE_FILE), *cmd]
    print(f"$ {' '.join(full)}")
    try:
        return subprocess.call(full)
    except FileNotFoundError:
        print("docker not found. Install Docker to stand up the live range; "
              "scenario/grading commands still work offline.", file=sys.stderr)
        return 127


def cmd_deploy(args) -> int:
    # Hard scope check: we only ever touch the loopback-bound compose project.
    safety.require_in_scope("localhost")
    seed = _resolve_seed(args)
    scenario = load_scenario(seed, args.state_dir)

    rc = _compose("up", "-d", "--build")
    if rc != 0:
        return rc

    # Plant the selected artifacts per service via the in-container dispatcher.
    by_service: dict[str, list[str]] = {}
    for f in scenario.findings:
        by_service.setdefault(f.service, []).append(f.artifact_id)

    for service, ids in by_service.items():
        print(f"\nPlanting {len(ids)} finding(s) in '{service}' ...")
        rc = _compose(
            "exec", "-T", service,
            "/opt/beaconhunt/plant/plant-dispatch.sh", *ids,
        )
        if rc != 0:
            print(f"warning: planting in {service} returned {rc}", file=sys.stderr)
    print("\nRange is up. Start hunting, then `beaconhunt submit` your findings.")
    return 0


def cmd_submit(args) -> int:
    seed = _resolve_seed(args)
    cat = load_catalog(args.catalog)
    # Validate claimed service/category against known values for a helpful error.
    state = load_round(seed, args.state_dir)
    state.submissions.append(
        Submission(
            type=args.type or "",
            service=args.service or "",
            evidence=args.evidence,
            at=time.time(),
        )
    )
    save_round(state, args.state_dir)
    print(f"Recorded submission #{len(state.submissions)}: "
          f"[{args.service or '?'}/{args.type or '?'}] {args.evidence}")
    _ = cat  # catalog loaded to surface schema errors early
    return 0


def cmd_hint(args) -> int:
    seed = _resolve_seed(args)
    cat = load_catalog(args.catalog)
    scenario = load_scenario(seed, args.state_dir)
    state = load_round(seed, args.state_dir)

    hint = choose_hint(cat, scenario, state, service=args.service)
    if hint is None:
        print("No findings match that filter.")
        return 0
    state.hints_used[hint["artifact_id"]] = hint["n"] + 1
    save_round(state, args.state_dir)
    print(f"[hint {hint['n'] + 1} for a {hint['service']}/{hint['category']} "
          f"finding, costs ~{hint['cost']} pts]")
    print(f"  {hint['text']}")
    return 0


def cmd_grade(args) -> int:
    seed = _resolve_seed(args)
    cat = load_catalog(args.catalog)
    scenario = load_scenario(seed, args.state_dir)
    state = load_round(seed, args.state_dir)
    if state.finished_at is None:
        state.finished_at = time.time()
        save_round(state, args.state_dir)

    result = grade(scenario, cat, state.submissions, state.hints_used)
    text = report.render_text(result, cat, scenario, state.elapsed)
    print(text)

    if not args.no_record:
        entry = scoreboard.record(result, state.elapsed, args.state_dir)
        print(f"\nRecorded to scoreboard: {entry.final_points} pts, "
              f"detection rate {int(entry.detection_rate * 100)}%.")
    return 0


def cmd_reveal(args) -> int:
    seed = _resolve_seed(args)
    cat = load_catalog(args.catalog)
    scenario = load_scenario(seed, args.state_dir)
    print(f"ANSWER KEY — scenario seed {seed} ({len(scenario.findings)} findings)\n")
    for f in scenario.findings:
        art = cat.get(f.artifact_id)
        print(learning.explain(art))
        print()
    return 0


def cmd_learn(args) -> int:
    cat = load_catalog(args.catalog)
    if args.artifact_id:
        try:
            print(learning.explain(cat.get(args.artifact_id)))
        except KeyError:
            sys.exit(f"no such artifact: {args.artifact_id}")
        return 0
    print(learning.walkthrough(cat, service=args.service))
    return 0


def cmd_scoreboard(args) -> int:
    entries = scoreboard.load(args.state_dir)
    if not entries:
        print("No rounds recorded yet.")
        return 0
    print(f"{'seed':>10}  {'score':>12}  {'detect':>7}  {'FP':>3}  {'time':>7}")
    print("-" * 48)
    for e in entries:
        print(f"{e.seed:>10}  {e.final_points:>5}/{e.total_possible:<6}  "
              f"{int(e.detection_rate * 100):>6}%  {e.false_positives:>3}  "
              f"{int(e.elapsed_seconds):>5}s")
    best = max(entries, key=lambda e: e.final_points)
    print(f"\nBest: {best.final_points} pts (seed {best.seed}).")
    return 0


def cmd_web(args) -> int:
    from . import webui
    return webui.serve(
        args.catalog, args.state_dir, port=args.port,
        user=args.user, password=args.password, auth=not args.no_auth,
    )


def cmd_teardown(args) -> int:
    safety.require_in_scope("localhost")
    return _compose("down", "-v")


def cmd_reset(args) -> int:
    safety.require_in_scope("localhost")
    rc = _compose("down", "-v")
    if rc not in (0, 127):
        return rc
    return cmd_deploy(args)


# --------------------------------------------------------------------------- #
# arg parsing
# --------------------------------------------------------------------------- #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="beaconhunt",
        description="BeaconHunt — contained blue-team detection training range.",
    )
    p.add_argument("--version", action="version", version=f"beaconhunt {__version__}")
    p.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_DIR,
                   help="catalog directory (default: ./catalog)")
    p.add_argument("--state-dir", type=Path, default=STATE_DIR,
                   help="state directory (default: ./state)")
    sub = p.add_subparsers(dest="command", required=True)

    def add_filters(sp):
        sp.add_argument("--service")
        sp.add_argument("--category")
        sp.add_argument("--difficulty", choices=["easy", "medium", "hard"])

    sp = sub.add_parser("catalog", help="list catalog artifacts")
    add_filters(sp)
    sp.set_defaults(func=cmd_catalog)

    sp = sub.add_parser("generate", help="generate a (seedable) scenario")
    sp.add_argument("--seed", type=int)
    sp.add_argument("--count", type=int, default=5)
    add_filters(sp)
    sp.set_defaults(func=cmd_generate)

    sp = sub.add_parser("deploy", help="stand up the range and plant findings")
    sp.add_argument("--seed", type=int)
    sp.set_defaults(func=cmd_deploy)

    sp = sub.add_parser("submit", help="submit a finding")
    sp.add_argument("--seed", type=int)
    sp.add_argument("--type", help="claimed category (backdoor, beacon, ...)")
    sp.add_argument("--service", help="claimed service (ssh, web, ...)")
    sp.add_argument("--evidence", required=True,
                    help="path / PID / port / user / config line")
    sp.set_defaults(func=cmd_submit)

    sp = sub.add_parser("hint", help="reveal a hint (costs points)")
    sp.add_argument("--seed", type=int)
    sp.add_argument("--service")
    sp.set_defaults(func=cmd_hint)

    sp = sub.add_parser("grade", help="score the round and print the report")
    sp.add_argument("--seed", type=int)
    sp.add_argument("--no-record", action="store_true")
    sp.set_defaults(func=cmd_grade)

    sp = sub.add_parser("reveal", help="reveal the answer key (give up / learn)")
    sp.add_argument("--seed", type=int)
    sp.set_defaults(func=cmd_reveal)

    sp = sub.add_parser("learn", help="explainers and hunt walkthrough")
    sp.add_argument("artifact_id", nargs="?")
    sp.add_argument("--service")
    sp.set_defaults(func=cmd_learn)

    sp = sub.add_parser("scoreboard", help="show round history")
    sp.set_defaults(func=cmd_scoreboard)

    sp = sub.add_parser("web", help="launch the local submission web UI (127.0.0.1)")
    sp.add_argument("--port", type=int, default=8800)
    sp.add_argument("--user", default="hunter", help="sign-in username (default: hunter)")
    sp.add_argument("--password", default=None,
                    help="sign-in password (default: $BEACONHUNT_WEB_PASSWORD or a "
                         "random one printed at startup)")
    sp.add_argument("--no-auth", action="store_true",
                    help="disable the login (localhost only; not recommended)")
    sp.set_defaults(func=cmd_web)

    sp = sub.add_parser("teardown", help="tear the range down")
    sp.set_defaults(func=cmd_teardown)

    sp = sub.add_parser("reset", help="tear down and redeploy fresh")
    sp.add_argument("--seed", type=int)
    sp.set_defaults(func=cmd_reset)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
