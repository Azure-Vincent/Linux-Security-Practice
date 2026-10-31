"""Offline tests for the BeaconHunt engine (no Docker required)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from beaconhunt import safety  # noqa: E402
from beaconhunt.catalog import load_catalog  # noqa: E402
from beaconhunt.grader import Submission, grade  # noqa: E402
from beaconhunt.report import render_text  # noqa: E402
from beaconhunt.scenario import generate_scenario  # noqa: E402
from beaconhunt.schema import SchemaError, parse_artifact  # noqa: E402

CATALOG_DIR = REPO_ROOT / "catalog"


@pytest.fixture(scope="module")
def catalog():
    return load_catalog(CATALOG_DIR)


# ----------------------------- schema --------------------------------------- #

def test_catalog_loads_and_validates(catalog):
    assert len(catalog) >= 5
    assert "ssh" in catalog.services
    art = catalog.get("ssh-authorized-keys-backdoor")
    assert art.category == "backdoor"
    assert art.points == 100
    assert art.signatures  # answer key present


def test_schema_rejects_bad_category():
    with pytest.raises(SchemaError):
        parse_artifact({
            "id": "x", "name": "x", "service": "ssh", "category": "nope",
            "difficulty": "easy", "points": 10,
            "description": "d",
            "detection": {"signatures": [{"type": "file_exists", "path": "/x"}]},
        })


def test_schema_requires_signatures():
    with pytest.raises(SchemaError):
        parse_artifact({
            "id": "x", "name": "x", "service": "ssh", "category": "backdoor",
            "difficulty": "easy", "points": 10, "description": "d",
            "detection": {"signatures": []},
        })


# ----------------------------- safety --------------------------------------- #

@pytest.mark.parametrize("target", ["localhost", "127.0.0.1", "::1", "ssh", "beaconhunt-ssh"])
def test_safety_allows_local(target):
    assert safety.classify_target(target).allowed


@pytest.mark.parametrize("target", ["8.8.8.8", "example.com", "github.com:443"])
def test_safety_refuses_external(target):
    decision = safety.classify_target(target)
    assert not decision.allowed
    with pytest.raises(safety.ScopeViolation):
        decision.enforce()


# ----------------------------- scenario ------------------------------------- #

def test_scenario_is_reproducible_by_seed(catalog):
    a = generate_scenario(catalog, seed=1337, count=3, services=["ssh"])
    b = generate_scenario(catalog, seed=1337, count=3, services=["ssh"])
    assert [f.artifact_id for f in a.findings] == [f.artifact_id for f in b.findings]
    assert a.total_points == b.total_points


def test_scenario_respects_filters(catalog):
    s = generate_scenario(catalog, seed=1, count=10, services=["ssh"],
                          categories=["backdoor"])
    assert all(f.service == "ssh" and f.category == "backdoor" for f in s.findings)


# ----------------------------- grading -------------------------------------- #

def test_grade_true_positive_and_missed(catalog):
    scenario = generate_scenario(catalog, seed=1337, count=3, services=["ssh"])
    first = scenario.findings[0]
    art = catalog.get(first.artifact_id)
    evidence = art.accept_evidence.paths[0]
    subs = [Submission(type=first.category, service="ssh", evidence=evidence)]
    result = grade(scenario, catalog, subs)
    assert result.true_positives == 1
    assert result.scored[0].matched_artifact_id == first.artifact_id
    assert result.scored[0].strength == "strong"
    assert len(result.missed) == len(scenario.findings) - 1
    assert result.final_points == art.points


def test_grade_false_positive_penalized(catalog):
    scenario = generate_scenario(catalog, seed=1337, count=2, services=["ssh"])
    subs = [Submission(type="backdoor", service="ssh",
                       evidence="/tmp/definitely-not-a-finding")]
    result = grade(scenario, catalog, subs)
    assert result.false_positives == 1
    assert result.false_positive_penalty > 0
    assert result.final_points == 0


def test_grade_service_mismatch_is_false_positive(catalog):
    scenario = generate_scenario(catalog, seed=1337, count=3, services=["ssh"])
    art = catalog.get(scenario.findings[0].artifact_id)
    # Right evidence, wrong claimed service -> should not credit.
    subs = [Submission(type=art.category, service="web",
                       evidence=art.accept_evidence.paths[0])]
    result = grade(scenario, catalog, subs)
    assert result.true_positives == 0
    assert result.false_positives == 1


def test_hint_penalty_applied(catalog):
    scenario = generate_scenario(catalog, seed=1337, count=2, services=["ssh"])
    first = scenario.findings[0]
    art = catalog.get(first.artifact_id)
    subs = [Submission(type=first.category, service="ssh",
                       evidence=art.accept_evidence.paths[0])]
    result = grade(scenario, catalog, subs, hints_used={first.artifact_id: 1})
    assert result.hint_penalty > 0
    assert result.final_points < art.points


def test_web_service_catalog(catalog):
    assert "web" in catalog.services
    web = catalog.filter(service="web")
    assert len(web) >= 5
    cats = {a.category for a in web}
    assert {"backdoor", "misconfig", "weak-cred", "beacon", "privesc"} <= cats


def test_web_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=42, count=5, services=["web"])
    art = catalog.get("web-php-webshell")
    subs = [Submission(type="backdoor", service="web",
                       evidence=art.accept_evidence.paths[0])]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "web-php-webshell"
    assert result.scored[0].strength == "strong"


def test_db_service_catalog(catalog):
    assert "db" in catalog.services
    db = catalog.filter(service="db")
    assert len(db) >= 5
    cats = {a.category for a in db}
    assert {"backdoor", "weak-cred", "misconfig", "privesc", "persistence"} <= cats


def test_db_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=7, count=5, services=["db"])
    subs = [Submission(type="backdoor", service="db",
                       evidence="rogue user dbsupport with ALL PRIVILEGES")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "db-rogue-admin-user"
    assert result.scored[0].strength == "strong"


def test_smb_service_catalog(catalog):
    assert "smb" in catalog.services
    smb = catalog.filter(service="smb")
    assert len(smb) >= 5
    cats = {a.category for a in smb}
    assert {"misconfig", "backdoor", "weak-cred", "persistence", "beacon"} <= cats


def test_smb_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=5, count=5, services=["smb"])
    subs = [Submission(type="backdoor", service="smb",
                       evidence="/srv/public/update.sh")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "smb-planted-dropzone"
    assert result.scored[0].strength == "strong"


def test_mail_service_catalog(catalog):
    assert "mail" in catalog.services
    mail = catalog.filter(service="mail")
    assert len(mail) >= 5
    cats = {a.category for a in mail}
    assert {"misconfig", "weak-cred", "backdoor", "persistence", "beacon"} <= cats


def test_mail_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=11, count=5, services=["mail"])
    subs = [Submission(type="backdoor", service="mail",
                       evidence="/etc/aliases pipe to mailhook")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "mail-alias-backdoor"
    assert result.scored[0].strength == "strong"


def test_redis_service_catalog(catalog):
    assert "redis" in catalog.services
    rds = catalog.filter(service="redis")
    assert len(rds) >= 5
    cats = {a.category for a in rds}
    assert {"misconfig", "weak-cred", "backdoor", "persistence", "beacon"} <= cats


def test_redis_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=4, count=5, services=["redis"])
    subs = [Submission(type="backdoor", service="redis",
                       evidence="rogue key beaconhunt:backdoor")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "redis-rogue-key"
    assert result.scored[0].strength == "strong"


def test_dns_service_catalog(catalog):
    assert "dns" in catalog.services
    dns = catalog.filter(service="dns")
    assert len(dns) >= 5
    cats = {a.category for a in dns}
    assert {"misconfig", "backdoor", "weak-cred", "beacon"} <= cats


def test_dns_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=8, count=5, services=["dns"])
    subs = [Submission(type="backdoor", service="dns",
                       evidence="rogue record in /etc/bind/db.acme.local")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "dns-rogue-record"
    assert result.scored[0].strength == "strong"


def test_matcher_prefers_keyword_corroborated(catalog):
    # Two findings share /etc/bind; the evidence's keyword should disambiguate.
    scenario = generate_scenario(catalog, seed=8, count=5, services=["dns"])
    subs = [Submission(type="misconfig", service="dns",
                       evidence="allow-transfer any in /etc/bind/named.conf.options")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "dns-zone-transfer-any"


def test_ftp_service_catalog(catalog):
    assert "ftp" in catalog.services
    ftp = catalog.filter(service="ftp")
    assert len(ftp) >= 5
    cats = {a.category for a in ftp}
    assert {"misconfig", "weak-cred", "backdoor", "privesc", "beacon"} <= cats


def test_ftp_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=3, count=5, services=["ftp"])
    subs = [Submission(type="backdoor", service="ftp",
                       evidence="/srv/ftp/upload/update.sh")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "ftp-planted-backdoor"
    assert result.scored[0].strength == "strong"


def test_host_service_catalog(catalog):
    assert "host" in catalog.services
    host = catalog.filter(service="host")
    assert len(host) >= 5
    cats = {a.category for a in host}
    assert {"backdoor", "privesc", "persistence", "misconfig", "beacon"} <= cats


def test_host_grade_true_positive(catalog):
    scenario = generate_scenario(catalog, seed=9, count=5, services=["host"])
    subs = [Submission(type="backdoor", service="host",
                       evidence="toor uid 0 in /etc/passwd")]
    result = grade(scenario, catalog, subs)
    assert result.scored[0].matched_artifact_id == "host-uid0-account"
    assert result.scored[0].strength == "strong"


def test_report_renders(catalog):
    scenario = generate_scenario(catalog, seed=1337, count=3, services=["ssh"])
    result = grade(scenario, catalog, [])
    text = render_text(result, catalog, scenario, elapsed_seconds=42)
    assert "Round Report" in text
    assert "MISSED FINDINGS" in text
