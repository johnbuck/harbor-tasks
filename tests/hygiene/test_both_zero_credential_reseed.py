"""Fixture-reseed checks for the both-zero fix on
``tasks/compliance-security/credential-leak-detection`` (spec
2026-06-25-both-zero-grader-fixes, Fix 2).

The four "real" secret fixtures were seeded with RECOGNIZABLE example/placeholder
values that the instruction explicitly tells the agent NOT to flag — the AWS-docs
example key pair, an ``example.com`` DB host, an ``EXAMPLE…NOTREAL`` PEM body, and
the jwt.io default token. A precise agent correctly rejects all four and scores 0,
so ground truth contradicts the instruction.

These assert the fixtures are reseeded with realistic, NON-canonical fakes that are
still obviously secret-shaped but appear on no "known placeholder" list. They read
the real repo fixtures (no docker). The constants below are the well-known PUBLIC
example values being scrubbed — not real credentials.

RED expectation: every assertion currently FAILS because the canonical
example/placeholder value is still present in the fixture.
"""
import re

from helpers import REPO_ROOT

REPO = (REPO_ROOT / "tasks/compliance-security/credential-leak-detection"
        / "environment/repo")

# Well-known public placeholder values the instruction says NOT to flag.
AWS_EXAMPLE_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_EXAMPLE_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
JWT_IO_DEFAULT_SIG = "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"


def _read(relpath: str) -> str:
    return (REPO / relpath).read_text(errors="replace")


def test_config_aws_key_realistic_not_docs_example():
    """config.py must carry an AWS-shaped access-key/secret pair that is NOT the
    AWS-documentation example (``AKIAIOSFODNN7EXAMPLE`` / ``…EXAMPLEKEY``), and no
    bare ``EXAMPLE`` marker — yet still looks like a real key (AKIA + 16)."""
    text = _read("config.py")
    assert AWS_EXAMPLE_KEY_ID not in text, "config.py still uses the AWS docs example key id"
    assert AWS_EXAMPLE_SECRET not in text, "config.py still uses the AWS docs example secret"
    assert "EXAMPLE" not in text, "config.py still contains an EXAMPLE placeholder marker"
    assert re.search(r"AKIA[0-9A-Z]{16}", text), "config.py no longer carries an AWS-shaped key id"


def test_db_host_is_synthetic_not_example_com():
    """db.py's DATABASE_URL must use a plausible synthetic internal host (NOT the
    ``example.com`` reserved placeholder domain) while still embedding a password."""
    text = _read("db.py")
    assert "example.com" not in text, "db.py DB host still uses the example.com placeholder domain"
    m = re.search(r"postgres://[^:@\s]+:[^@\s]+@([^:/\s]+)", text)
    assert m, "db.py no longer embeds a password in the connection string"
    assert not m.group(1).endswith("example.com"), m.group(1)


def test_auth_jwt_is_not_jwtio_default():
    """auth.py's committed JWT must not be the jwt.io default token (signature
    ``SflKxw…ssw5c``) while still being a JWT (three ``eyJ``-style segments)."""
    text = _read("auth.py")
    assert JWT_IO_DEFAULT_SIG not in text, "auth.py still embeds the jwt.io default token"
    assert re.search(r"eyJ[A-Za-z0-9_-]+\.", text), "auth.py no longer carries a JWT-shaped token"


def test_id_rsa_pem_body_has_no_placeholder_markers():
    """deploy/id_rsa must be a realistic PEM body with no ``EXAMPLE`` / ``NOTREAL``
    placeholder markers, while still being a private key block."""
    text = _read("deploy/id_rsa")
    assert "EXAMPLE" not in text, "id_rsa still contains an EXAMPLE placeholder marker"
    assert "NOTREAL" not in text, "id_rsa still contains a NOTREAL placeholder marker"
    assert "PRIVATE KEY" in text, "id_rsa is no longer a PEM private-key block"


def test_secret_files_carry_no_canonical_placeholder_values():
    """Belt-and-suspenders: none of the four real-secret fixtures may contain any
    of the known canonical placeholder strings the instruction says not to flag."""
    canonical = (AWS_EXAMPLE_KEY_ID, AWS_EXAMPLE_SECRET, JWT_IO_DEFAULT_SIG,
                 "example.com", "NOTREAL")
    offenders = {}
    for relpath in ("config.py", "db.py", "auth.py", "deploy/id_rsa"):
        text = _read(relpath)
        hits = [c for c in canonical if c in text]
        if hits:
            offenders[relpath] = hits
    assert not offenders, offenders
