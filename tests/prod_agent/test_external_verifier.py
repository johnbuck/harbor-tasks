"""Offline unit checks for ExternalTranscriptVerifier.verify (lib.external_verifier).

Encodes spec success criterion #6: verify() reads agent_dir/external.txt, grades
it via the task's host-side rewardkit grader, returns a VerifierResult with a
flat numeric reward, and emits answer_present=0 (a VOID, not a false 0.0 loss)
when the transcript is missing.

The grader is a REAL rewardkit grader fixture (grader_fixture/reward.py) run on
the host — not mocked. Each test copies the fixture to a UNIQUE tests_dir so the
rewardkit per-path module cache cannot bleed criteria between tests.
"""
import shutil
from pathlib import Path

from harbor.models.trial.paths import TrialPaths
from harbor.models.verifier.result import VerifierResult

from prod_agent_support import run_async

_FIXTURE = Path(__file__).resolve().parent / "grader_fixture"


def _make_verifier(tmp_path, transcript_text):
    """Stage a trial dir (+ optional transcript) and a unique grader dir."""
    trial_paths = TrialPaths(trial_dir=tmp_path / "trial")
    trial_paths.mkdir()
    if transcript_text is not None:
        (trial_paths.agent_dir / "external.txt").write_text(transcript_text)

    grader_dir = tmp_path / "grader"
    shutil.copytree(_FIXTURE, grader_dir)

    import lib.external_verifier as ev  # lazy: missing module -> this test only

    return ev.ExternalTranscriptVerifier(
        task=None,
        trial_paths=trial_paths,
        environment=None,
        tests_dir=str(grader_dir),
        answer_filename="answer.md",
    )


def test_verify_grades_present_correct_transcript(tmp_path):
    verifier = _make_verifier(tmp_path, "The capital is Paris.")
    result = run_async(verifier.verify())

    assert isinstance(result, VerifierResult)
    rewards = result.rewards
    assert rewards is not None
    assert all(isinstance(v, (int, float)) for v in rewards.values()), (
        "reward.json must be a FLAT dict of numbers (FOOTGUN #2)"
    )
    assert rewards.get("reward") == 1.0
    assert rewards.get("answer_present") == 1


def test_verify_grades_present_but_wrong_transcript_as_loss_not_void(tmp_path):
    verifier = _make_verifier(tmp_path, "The capital is London.")
    result = run_async(verifier.verify())

    rewards = result.rewards
    assert rewards.get("reward") == 0.0
    # Present-but-wrong is a real 0.0 LOSS, distinguished from a VOID.
    assert rewards.get("answer_present") == 1


def test_verify_missing_transcript_emits_answer_present_zero(tmp_path):
    verifier = _make_verifier(tmp_path, transcript_text=None)
    result = run_async(verifier.verify())

    rewards = result.rewards
    assert rewards is not None
    # A missing transcript is a VOID (answer_present=0), NOT a false 0.0 loss.
    assert rewards.get("answer_present") == 0
