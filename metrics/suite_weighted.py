"""Suite post-run analyzer: weighted aggregate + harness SPLIT + pass^k.

WHY NOT A MetricType.UV_SCRIPT?
Harbor's metric API receives `list[RewardDict | None]` — just the rewards, no
task names. We need to look up each task's category (for weighting) and
difficulty (for tier breakdown), which means walking the jobs/ tree and reading
each trial's task.toml. That's a post-run analyzer, not a metric.

GOAL (spec §Goal — Definition of Done): prove the suite tells harness quality
apart from model quality. Both harnesses run the SAME model, so the headline
number is the **split** — openclaw_weighted − hermes_weighted — and whether it
clears the ≥10% bar reliably under pass^k. This analyzer computes:

  * per-agent weighted aggregate (Σ weight·score / Σ weight), where each TASK
    contributes once (its pass-rate over n attempts), so n_attempts never skews
    the category means;
  * pass^k reliability (τ-bench style): pass^1 = mean pass rate, pass^k =
    fraction of tasks where ALL k attempts pass. Degrades to pass^1 at n=1.
  * the SPLIT: overall + per-category deltas between the two harnesses, sorted
    by magnitude, with a `meets_10pct` flag;
  * per-task discrimination: openclaw vs hermes per task — the diagnostic table
    that drives #79 (blunt vs too-hard vs genuine-tie) and the weight refit.

Read flow:
  jobs/<job>/<trial>/result.json      → agent_info.name + task_name + rewards
  tasks/<cat>/<name>/task.toml        → [metadata].category + .difficulty
  configs/suite-weights.toml        → per-category weight multipliers

Write flow:
  jobs/<job>/suite_report.json      → {agents, split, per_task_discrimination}

USAGE:
  uv run metrics/suite_weighted.py \
      --job-dir /tmp/harbor-jobs/suite-sweep-1 \
      --tasks-root <repo>/tasks \
      --weights configs/suite-weights.toml [--pass-threshold 1.0]
"""

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from collections import defaultdict
from math import comb
from pathlib import Path
from typing import Any

# A trial "passes" when its reward meets this threshold. Most verifiers emit
# reward ∈ {0,1}; multi-step "final" rewards can be fractional, so full success
# (1.0) is the default bar for the binary pass^k. Mean reward is reported too.
DEFAULT_PASS_THRESHOLD = 1.0

# ---- Effective-reward policy (operator-set 2026-05-31) ---------------------
# A crashed or timed-out agent did NOT cleanly succeed, even if the verifier
# happened to read good filesystem state. The raw verifier reward is too
# lenient (a SIGABRT that still scores 1.0 hides a real reliability failure).
# Penalize by COMPLETION:
#   crash / timeout  +  work COMPLETE   -> 0.5  (deliverable landed, process died)
#   crash / timeout  +  work INCOMPLETE -> 0.0  (failed run)
# "complete" = the verifier still scored a full pass (raw reward >= threshold).
# A 0.5 is below the pass threshold, so it correctly fails pass^k — that is the
# reliability signal. Clean (no-exception) trials keep their raw reward.
CRASH_OR_TIMEOUT_COMPLETE_REWARD = 0.5

# Exception types that mean the agent PROCESS failed (vs. the model just doing
# poorly). NonZeroAgentExitCode covers SIGABRT/segfault (exit 134/139).
_CRASH_EXC = {"NonZeroAgentExitCodeError", "AgentCrashError"}
_TIMEOUT_EXC = {"AgentTimeoutError"}


def _trial_exception_types(tr: dict[str, Any]) -> set[str]:
    """All exception types in a trial — top-level and every step."""
    types: set[str] = set()
    top = tr.get("exception_info")
    if top and top.get("exception_type"):
        types.add(top["exception_type"])
    for s in tr.get("step_results") or []:
        e = (s or {}).get("exception_info")
        if e and e.get("exception_type"):
            types.add(e["exception_type"])
    return types


def _classify_trial(tr: dict[str, Any], pass_threshold: float) -> dict[str, Any]:
    """Return {raw, effective, status} applying the crash/timeout penalty.

    status ∈ clean | partial | fail | crash_complete | crash_incomplete |
            timeout_complete | timeout_incomplete | no_reward
    """
    raw = _reward_value((tr.get("verifier_result") or {}).get("rewards"))
    if raw is None and (tr.get("step_results") or []):  # multi-step "final"
        raw = _reward_value(
            ((tr["step_results"][-1].get("verifier_result")) or {}).get("rewards"))

    types = _trial_exception_types(tr)
    crashed = bool(types & _CRASH_EXC)
    timed_out = bool(types & _TIMEOUT_EXC)
    complete = raw is not None and raw >= pass_threshold

    if crashed or timed_out:
        kind = "crash" if crashed else "timeout"
        if complete:
            return {"raw": raw, "effective": CRASH_OR_TIMEOUT_COMPLETE_REWARD,
                    "status": f"{kind}_complete"}
        return {"raw": raw, "effective": 0.0, "status": f"{kind}_incomplete"}

    if raw is None:  # no usable score (e.g. verifier ValidationError) and no crash
        return {"raw": None, "effective": 0.0, "status": "no_reward"}
    status = "clean" if complete else ("partial" if raw > 0 else "fail")
    return {"raw": raw, "effective": raw, "status": status}


def _canonical_agent(name: str | None) -> str:
    """Normalize runtime agent names to a stable harness label."""
    n = (name or "unknown").strip().lower()
    if n.startswith("openclaw"):
        return "openclaw"
    if n.startswith("hermes"):
        return "hermes"
    return n


def _load_weights(path: Path) -> dict[str, float]:
    if not path.exists():
        print(f"weights file {path} missing — using all weights = 1.0", file=sys.stderr)
        return defaultdict(lambda: 1.0)
    data = tomllib.loads(path.read_text())
    return defaultdict(lambda: 1.0, data.get("weights", {}))


def _task_metadata(task_dir: Path) -> dict[str, str]:
    """Read [metadata] from a task.toml; returns {} on any failure."""
    toml_path = task_dir / "task.toml"
    if not toml_path.exists():
        return {}
    try:
        data = tomllib.loads(toml_path.read_text())
    except Exception:
        return {}
    return data.get("metadata", {})


def _reward_value(reward: Any) -> float | None:
    """Extract a single scalar from a reward dict; prefers 'reward' key."""
    if reward is None:
        return None
    if isinstance(reward, dict):
        if "reward" in reward:
            v = reward["reward"]
        elif len(reward) == 1:
            v = next(iter(reward.values()))
        else:
            return None
        return float(v) if isinstance(v, int | float) else None
    if isinstance(reward, int | float):
        return float(reward)
    return None


def _resolve_task_dir(task_name: str, tasks_root: Path) -> Path | None:
    """Map a Harbor task_name (often '<org>/<shape>-<NN>') to its directory."""
    short = task_name.split("/", 1)[-1]
    matches = list(tasks_root.glob(f"*/{short}"))
    return matches[0] if matches else None


def _trial_efficiency(tr: dict[str, Any]) -> dict[str, float]:
    """Sum cost + tokens across a trial's step_results[*].agent_result.

    Efficiency is a SECOND discrimination axis: two harnesses can tie on reward
    while one burns far more tokens for the same result — a real harness-quality
    difference (rich scaffolds are context-heavy). Returns zeros if absent.
    """
    cost = inp = out = cache = 0.0
    for step in tr.get("step_results") or []:
        ar = (step or {}).get("agent_result") or {}
        cost += ar.get("cost_usd") or 0.0
        inp += ar.get("n_input_tokens") or 0.0
        out += ar.get("n_output_tokens") or 0.0
        cache += ar.get("n_cache_tokens") or 0.0
    return {"cost_usd": cost, "input_tokens": inp,
            "output_tokens": out, "cache_tokens": cache,
            "total_tokens": inp + out + cache}


def _pass_at_k(n: int, c: int, k: int) -> float:
    """τ-bench pass^k: probability that k attempts drawn (without replacement)
    from n total all pass, given c of them passed. C(c,k)/C(n,k)."""
    if k > n or k <= 0 or n <= 0:
        return 0.0
    if c < k:
        return 0.0
    return comb(c, k) / comb(n, k)


def analyze(
    job_dirs: Path | list[Path],
    tasks_root: Path,
    weights_path: Path,
    pass_threshold: float = DEFAULT_PASS_THRESHOLD,
) -> dict[str, Any]:
    weights = _load_weights(weights_path)
    # Accept one dir or several (one job per harness — the canonical layout).
    # Trials are grouped by agent_info.name regardless of which dir they came
    # from, so the split works whether both harnesses are in one job or split
    # across two per-harness jobs.
    if isinstance(job_dirs, Path):
        job_dirs = [job_dirs]
    existing = [d for d in job_dirs if d.exists()]
    if not existing:
        raise FileNotFoundError(f"no job dirs exist among {job_dirs}")

    # Each trial is one <trial>/result.json. With n_attempts>1 there are several
    # subdirs per (agent, task); we group them below for pass^k.
    trial_results = [
        json.loads(p.read_text())
        for d in existing
        for p in sorted(d.glob("*/result.json"))
    ]
    if not trial_results:
        raise FileNotFoundError(f"no <trial>/result.json files under {existing}")

    # Collect per-trial rewards + efficiency keyed by (agent, task); also
    # remember each task's category + difficulty. We track the EFFECTIVE reward
    # (post crash/timeout penalty) for scoring AND the RAW reward so the report
    # can show how much the penalty moved each harness.
    attempts: dict[tuple[str, str], list[float]] = defaultdict(list)
    raw_attempts: dict[tuple[str, str], list[float]] = defaultdict(list)
    eff_attempts: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    # Per-agent reliability tally: status -> count.
    reliability: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    task_meta: dict[str, dict[str, str]] = {}
    for tr in trial_results:
        agent = _canonical_agent((tr.get("agent_info") or {}).get("name"))
        task_name = tr.get("task_name") or ""
        cls = _classify_trial(tr, pass_threshold)
        reliability[agent][cls["status"]] += 1
        # Every trial counts now — a crash/no_reward is a real failed attempt,
        # not something to silently drop (dropping hid the reliability gap).
        attempts[(agent, task_name)].append(cls["effective"])
        raw_attempts[(agent, task_name)].append(
            cls["raw"] if cls["raw"] is not None else 0.0)
        eff_attempts[(agent, task_name)].append(_trial_efficiency(tr))
        if task_name not in task_meta:
            td = _resolve_task_dir(task_name, tasks_root)
            task_meta[task_name] = _task_metadata(td) if td else {}

    # Per-(agent, task) stats: mean reward (pass^1), pass^k reliability.
    # task_stats[agent][task] = {mean, pass1, passk, n, category, difficulty}
    task_stats: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    agents_seen: set[str] = set()
    for (agent, task), rewards in attempts.items():
        agents_seen.add(agent)
        n = len(rewards)
        c = sum(1 for r in rewards if r >= pass_threshold)
        meta = task_meta.get(task, {})
        effs = eff_attempts[(agent, task)]
        raws = raw_attempts[(agent, task)]
        mean_cost = sum(e["cost_usd"] for e in effs) / len(effs) if effs else 0.0
        mean_tokens = sum(e["total_tokens"] for e in effs) / len(effs) if effs else 0.0
        task_stats[agent][task] = {
            "mean": sum(rewards) / n,             # EFFECTIVE (post-penalty)
            "mean_raw": sum(raws) / len(raws) if raws else 0.0,  # pre-penalty
            "pass1": c / n,                       # = pass^1 (on effective)
            "passk": _pass_at_k(n, c, n),         # all-k-pass (k=n): strict reliability
            "n": n,
            "mean_cost_usd": mean_cost,
            "mean_total_tokens": mean_tokens,
            "category": meta.get("category", "uncategorized"),
            "difficulty": meta.get("difficulty", "unknown"),
        }

    # Per-agent report. Each TASK contributes once (its mean over attempts), so
    # n_attempts doesn't skew category means or the weighted aggregate.
    report: dict[str, Any] = {"agents": {}, "config": {
        "pass_threshold": pass_threshold,
        "n_trials_total": sum(len(v) for v in attempts.values()),
    }}
    for agent in sorted(agents_seen):
        stats = task_stats[agent]
        rows = list(stats.values())
        num = sum(weights[s["category"]] * s["mean"] for s in rows)
        den = sum(weights[s["category"]] for s in rows)
        weighted = num / den if den else 0.0
        # Same aggregate on RAW rewards — the gap to `weighted` is the penalty.
        raw_num = sum(weights[s["category"]] * s["mean_raw"] for s in rows)
        raw_weighted = raw_num / den if den else 0.0

        # Reliability tally → rates. error_rate = any non-clean execution.
        rel = dict(reliability[agent])
        n_tr = sum(rel.values()) or 1
        n_crash = rel.get("crash_complete", 0) + rel.get("crash_incomplete", 0)
        n_timeout = rel.get("timeout_complete", 0) + rel.get("timeout_incomplete", 0)
        n_noreward = rel.get("no_reward", 0)
        rel_block = {
            "counts": rel,
            "n_trials": sum(rel.values()),
            "crash_rate": n_crash / n_tr,
            "timeout_rate": n_timeout / n_tr,
            "error_rate": (n_crash + n_timeout + n_noreward) / n_tr,
        }

        per_cat: dict[str, dict[str, float]] = {}
        cat_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for s in rows:
            cat_groups[s["category"]].append(s)
        for cat, ss in cat_groups.items():
            per_cat[cat] = {
                "mean": sum(s["mean"] for s in ss) / len(ss),
                "pass1": sum(s["pass1"] for s in ss) / len(ss),
                "passk": sum(s["passk"] for s in ss) / len(ss),
                "n_tasks": len(ss),
                "weight": weights[cat],
            }

        per_diff: dict[str, dict[str, float]] = {}
        diff_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for s in rows:
            diff_groups[s["difficulty"]].append(s)
        for tier, ss in diff_groups.items():
            per_diff[tier] = {
                "mean": sum(s["mean"] for s in ss) / len(ss),
                "n_tasks": len(ss),
            }

        report["agents"][agent] = {
            "weighted_aggregate": weighted,
            "weighted_aggregate_raw": raw_weighted,
            "penalty_delta": raw_weighted - weighted,  # how much crashes cost it
            "reliability": rel_block,
            "passk_aggregate": (sum(s["passk"] for s in rows) / len(rows)) if rows else 0.0,
            "n_tasks": len(rows),
            "n_trials": sum(s["n"] for s in rows),
            "total_cost_usd": sum(s["mean_cost_usd"] for s in rows),
            "mean_cost_per_task": (sum(s["mean_cost_usd"] for s in rows) / len(rows)) if rows else 0.0,
            "mean_tokens_per_task": (sum(s["mean_total_tokens"] for s in rows) / len(rows)) if rows else 0.0,
            "per_category": per_cat,
            "per_difficulty": per_diff,
        }

    # ---- THE SPLIT: openclaw − hermes (the goal's headline metric) ----
    a, b = "openclaw", "hermes"
    if a in report["agents"] and b in report["agents"]:
        oc, he = report["agents"][a], report["agents"][b]
        overall_delta = oc["weighted_aggregate"] - he["weighted_aggregate"]
        cats = set(oc["per_category"]) | set(he["per_category"])
        per_cat_split = []
        for cat in cats:
            ocm = oc["per_category"].get(cat, {}).get("mean")
            hem = he["per_category"].get(cat, {}).get("mean")
            if ocm is None or hem is None:
                continue
            per_cat_split.append({
                "category": cat,
                "openclaw": ocm,
                "hermes": hem,
                "delta": ocm - hem,
                "abs_delta": abs(ocm - hem),
                "weight": weights[cat],
            })
        per_cat_split.sort(key=lambda d: d["abs_delta"], reverse=True)
        # Efficiency split: same model, so a token/cost gap is a HARNESS gap.
        # ratio >1 means openclaw spends more than hermes for its results.
        oc_tok, he_tok = oc["mean_tokens_per_task"], he["mean_tokens_per_task"]
        oc_cost, he_cost = oc["mean_cost_per_task"], he["mean_cost_per_task"]
        report["split"] = {
            "overall_delta": overall_delta,
            "abs_overall_delta": abs(overall_delta),
            "meets_10pct": abs(overall_delta) >= 0.10,
            "leader": a if overall_delta > 0 else (b if overall_delta < 0 else "tie"),
            "passk_overall_delta": oc["passk_aggregate"] - he["passk_aggregate"],
            "efficiency": {
                "openclaw_tokens_per_task": oc_tok,
                "hermes_tokens_per_task": he_tok,
                "token_ratio_oc_over_he": (oc_tok / he_tok) if he_tok else None,
                "openclaw_cost_per_task": oc_cost,
                "hermes_cost_per_task": he_cost,
                "cost_ratio_oc_over_he": (oc_cost / he_cost) if he_cost else None,
            },
            "per_category": per_cat_split,
            "discriminating_categories_meeting_10pct": [
                d["category"] for d in per_cat_split if d["abs_delta"] >= 0.10
            ],
        }

        # ---- per-task discrimination: the #79 diagnostic table ----
        disc = []
        all_tasks = set(task_stats[a]) | set(task_stats[b])
        for task in all_tasks:
            sa = task_stats[a].get(task)
            sb = task_stats[b].get(task)
            if not sa or not sb:
                continue
            delta = sa["mean"] - sb["mean"]
            both_full = sa["mean"] >= pass_threshold and sb["mean"] >= pass_threshold
            both_zero = sa["mean"] == 0.0 and sb["mean"] == 0.0
            disc.append({
                "task": task,
                "category": sa["category"],
                "difficulty": sa["difficulty"],
                "openclaw": sa["mean"],
                "hermes": sb["mean"],
                "delta": delta,
                "abs_delta": abs(delta),
                "openclaw_tokens": sa["mean_total_tokens"],
                "hermes_tokens": sb["mean_total_tokens"],
                "openclaw_passk": sa["passk"],
                "hermes_passk": sb["passk"],
                # diagnosis: BLUNT = both ace it (no headroom to discriminate);
                # TOO_HARD = both flatline at 0; otherwise it separates.
                "diagnosis": ("BLUNT" if both_full else
                              "TOO_HARD" if both_zero else
                              "DISCRIMINATES" if abs(delta) >= 0.10 else "TIE"),
            })
        disc.sort(key=lambda d: d["abs_delta"], reverse=True)
        report["per_task_discrimination"] = disc
    else:
        report["split"] = {
            "note": f"need both '{a}' and '{b}'; saw {sorted(agents_seen)}",
        }

    return report


def _print_summary(report: dict[str, Any]) -> None:
    """Human-readable split summary to stderr (the JSON still goes to stdout)."""
    split = report.get("split", {})
    if "overall_delta" not in split:
        print(f"[split] {split.get('note','(incomplete)')}", file=sys.stderr)
        return
    lead = split["leader"]
    # Reliability first — crashes/timeouts now penalize the effective score.
    agents = report.get("agents", {})
    for name in ("openclaw", "hermes"):
        a = agents.get(name)
        if not a:
            continue
        rel = a.get("reliability", {})
        print(f"[RELIABILITY] {name:9s} error_rate={rel.get('error_rate',0):.0%} "
              f"(crash {rel.get('crash_rate',0):.0%}, timeout {rel.get('timeout_rate',0):.0%}) "
              f"| raw={a['weighted_aggregate_raw']:.3f} → "
              f"effective={a['weighted_aggregate']:.3f} "
              f"(−{a['penalty_delta']:.3f} from crashes) | "
              f"counts={dict(rel.get('counts',{}))}", file=sys.stderr)
    print(f"\n[SPLIT] overall Δ = {split['overall_delta']:+.3f} "
          f"(|Δ| {split['abs_overall_delta']:.3f}, "
          f"{'MEETS' if split['meets_10pct'] else 'below'} 10% bar) "
          f"— leader: {lead}  [on EFFECTIVE reward]", file=sys.stderr)
    eff = split.get("efficiency", {})
    tr = eff.get("token_ratio_oc_over_he")
    cr = eff.get("cost_ratio_oc_over_he")
    if tr is not None:
        print(f"[EFFICIENCY] tokens/task oc={eff['openclaw_tokens_per_task']:.0f} "
              f"he={eff['hermes_tokens_per_task']:.0f} (oc/he={tr:.2f}x) | "
              f"cost/task oc=${eff['openclaw_cost_per_task']:.4f} "
              f"he=${eff['hermes_cost_per_task']:.4f}"
              f"{f' (oc/he={cr:.2f}x)' if cr else ''}", file=sys.stderr)
    print("[SPLIT] per-category (sorted by |Δ|):", file=sys.stderr)
    for d in split["per_category"]:
        flag = "  <-- ≥10%" if d["abs_delta"] >= 0.10 else ""
        print(f"   {d['category']:24s} oc={d['openclaw']:.2f} he={d['hermes']:.2f} "
              f"Δ={d['delta']:+.2f} w={d['weight']}{flag}", file=sys.stderr)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--job-dir", required=True, type=Path, action="append",
                   help="job dir; repeat for per-harness jobs (one openclaw, one hermes)")
    p.add_argument("--tasks-root", required=True, type=Path)
    p.add_argument("--weights", required=True, type=Path)
    p.add_argument("--pass-threshold", type=float, default=DEFAULT_PASS_THRESHOLD)
    p.add_argument("--out", type=Path, default=None,
                   help="output JSON; default: <first-job-dir>/suite_report.json")
    args = p.parse_args()

    report = analyze(args.job_dir, args.tasks_root, args.weights, args.pass_threshold)
    out = args.out or (args.job_dir[0] / "suite_report.json")
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    _print_summary(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
