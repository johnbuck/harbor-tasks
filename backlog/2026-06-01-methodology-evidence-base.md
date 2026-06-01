# Methodology evidence base — is our harness-eval approach grounded? (2026-06-01)

Operator challenge: stop asserting methodology from LLM priors; show real published
evidence that this is how harness evaluation is actually done, or admit where it isn't.
Five parallel research passes (WebSearch + WebFetch, primary sources only). Each
load-bearing claim is graded **SUPPORTED / PARTIAL / INFERENCE** with citations, plus
the corrections the research forced.

---

## Claim 1 — "Harness quality is measurable separately from the model" → **SUPPORTED**

Hold the model fixed, vary the scaffold; the score moves materially.

- **Terminal-Bench 2.0 / Harbor** (Merrill, Shaw et al., Laude Institute, 2026,
  arXiv:2601.11868). *Explicitly* states "agent and model performance are hard to
  decouple" and builds **Terminus 2** as "a simple scaffold which serves as a neutral
  testbed." Controlled same-model swings: Claude Opus 4.5 = **57.8% (Terminus 2) vs
  52.1% (Claude Code) vs 51.9% (OpenHands)**; GPT-5.2 = 62.9% (Codex) vs 54.0%
  (Terminus 2). Harness moves the score 6–9 pts at fixed model. **This is the
  framework we're literally building on.** https://arxiv.org/html/2601.11868v1
- **Aider edit-format leaderboard** (Gauthier). Same model, different edit format:
  gemini-exp-1206 = 80.5% (whole) vs 69.2% (diff) ≈ 11 pts; o1-mini 70.7% vs 61.1%.
  https://aider.chat/docs/leaderboards/edit.html
- **METR capability-elicitation guidelines** (2024). Formalizes "spurious" (scaffold-
  fixable) vs "real" bottlenecks; "poor scaffolding or tooling" is named a *spurious*
  failure — a measurable harness deficit. https://metr.org/blog/2024-03-15-guidelines-for-capability-elicitation/

**Caveat the evidence forces:** magnitude is **bounded**. METR's elicitation-gap data
shows scaffolding's marginal contribution shrinks (sometimes to statistical
insignificance) once a model is already well-elicited. So the honest thesis is **"the
harness is a large, separately-attributable axis whose size depends on how well the
model is already elicited,"** NOT "the harness matters more than the model" universally.
The viral "same model 42%→78%" figure is a paywalled, uncited Substack claim — do NOT
use it as a citation; anchor on Terminal-Bench / Aider / METR.

## Claim 2 — "Reliability via pass^k, not single-run reward" → **SUPPORTED** (with a correction)

- **pass@k** origin: Chen et al. 2021 (HumanEval), OpenAI — = P(at least one of k samples
  passes). https://arxiv.org/abs/2107.03374
- **pass^k** is a REAL, named metric — introduced by **τ-bench (Sierra; Yao, Shinn,
  Razavi, Narasimhan, 2024)** = P(**all** k independent trials succeed); "captures the
  reliability of the agent." gpt-4o ~61% pass^1 → ~25% pass^8 on τ-retail.
  https://arxiv.org/abs/2406.12045
- Run-to-run pass/fail flips **even at temperature 0**: "On Randomness in Agentic Evals"
  (Bjarnason et al., KTH, 2026, arXiv:2602.07150); "Consistency Amplifies" (2026).
- Reliability is a distinct axis from capability: "Beyond pass@1: A Reliability Science
  Framework for Long-Horizon LLM Agents" (2026, arXiv:2603.29231) — adopts Pass^k,
  shows capability and reliability rankings **diverge**.
- Statistical underpinning: Anthropic "Adding Error Bars to Evals" (Miller, 2024,
  arXiv:2411.00640) — multiple samples per item, paired-difference, power analysis.

**CORRECTION (I had this wrong):** I previously attributed pass^k / run-variance to
**METR**. That is a **misattribution** — METR measures task-completion *horizon*, not
run-to-run reliability. The correct provenance is **Sierra/τ-bench** (term) + the 2026
academic papers (variance). Fix in memory `harbor-tasks-discrimination-methodology`.

## Claim 3 — "Telegraphing the trap invalidates the test" → **SUPPORTED** (it's my coinage for established concepts)

"Telegraphing" is my informal label; reviewers will expect the real vocabulary:
- **Construct validity** (the umbrella): Jacobs & Wallach "Measurement and Fairness"
  FAccT 2021; Raji et al. "Everything in the Whole Wide World Benchmark" NeurIPS 2021;
  Bowman & Dahl NAACL 2021; HELM (Liang et al. 2022). Telegraphing = mismatch between
  the declared construct ("latent capability to handle X") and what's actually measured
  ("instruction-following of the hint").
- **Mechanism = shortcut learning / Clever Hans**: Geirhos et al., *Nature Machine
  Intelligence* 2020 (arXiv:2004.07780).
- **Closest operational analog = contamination / answer-leakage**: leakage through the
  *prompt* rather than training set, same invalidation logic. "SWE-Bench Illusion"
  (2025, arXiv:2506.12286) shows the failure in an agent benchmark.
- **Agent-hijack benchmarks already embody the rule**: **AgentDojo** (Debenedetti et al.,
  ETH, NeurIPS 2024) gives the agent a *benign, unwarned* task; **InjecAgent** (Zhan et
  al., ACL 2024) shows the measured number **24% → 47%** when you DO signal the attack
  (a "hacking prompt"). Hard empirical proof that telegraphing moves the number.

**Action:** keep "telegraphing" as our informal label but, in RESULTS.md, name it
**"construct-validity threat via prompt-level answer leakage / shortcut induction"** and
cite AgentDojo + InjecAgent as the design precedent.

## Claim 4 — "Overflow the real context window to test harness context-management" → **PARTIAL** (calibration supported; the overflow protocol is a novel contribution)

- **Effective ≪ claimed window** is firmly established: RULER (NVIDIA 2024,
  arXiv:2404.06654) — "only half" of 32K-claimed models hold up at 32K. NoLiMa (Adobe,
  ICML 2025) — 11/13 "128K" models <50% baseline at 32K. Lost-in-the-Middle (Liu et al.
  2023). **Chroma "Context Rot" (2025)** — for ~1M-token models the knee is empirically
  ~**300–400k tokens**. https://research.trychroma.com/context-rot
- **Compaction/externalization is a harness concern**: Anthropic "Effective context
  engineering for AI agents" (2025) frames **compaction** as a system-level
  responsibility; SWE-agent ships history-processor truncation (`last_n_observations`).
  Emerging agent-memory benchmarks: UltraHorizon, Acon, AgentLongBench (2025–26).

**Corrections the evidence forces:**
1. **Calibrate to the EFFECTIVE window, not the 1M spec sheet.** deepseek-v4-pro's
   advertised 1M almost certainly degrades far earlier (Context Rot ⇒ ~300–400k knee for
   1M-class models). Sizing context-fill to ~1.3M is fine for *forcing overflow*, but the
   harness's job (and the model's degradation) **starts ~300–400k**, not at 1M. Note this
   in the task design; don't imply the model is healthy up to 1M.
2. **Overflow alone entangles model + harness.** A corpus past the window still tests
   model retrieval up to the compaction boundary. To isolate the *harness*, score **what
   survives compaction** (what the harness chose to keep/externalize/re-fetch), not only
   end-task success.
3. The "must overflow to test context-management" protocol is **not settled doctrine** —
   the agent-context-mgmt eval space is young/fragmented. Present our overflow design as a
   **well-motivated novel contribution**, not an application of an accepted standard.

## Claim 5 — "Pin the OpenRouter provider or the token/cost/cache A/B is contaminated" → **SUPPORTED** (necessary; not sufficient)

- **OpenRouter docs** confirm verbatim: one model is served by many upstreams; "by
  default, requests are load balanced across the top providers"; price/throughput/cache
  differ per provider; pin via `order` / `only` / `allow_fallbacks:false`.
  https://openrouter.ai/docs/guides/routing/provider-selection
- **Provider output variance is real**: OpenRouter "Exacto" announcement — tool-call
  propensity/accuracy "vary between providers significantly"; dominant cause is the
  inference-engine/tool-parser, **not** quantization alone (don't over-lean on "diff
  quant").
- **Caching is provider-specific** (OpenRouter prompt-caching docs) → unpinned cost/cache
  comparison is contaminated, full stop.
- **But pinning is necessary, not sufficient**: Thinking Machines "Defeating
  Nondeterminism in LLM Inference" (He et al., 2025) — batch-size variance makes even one
  pinned provider nondeterministic at temp 0; CISPA "The Silent Hyperparameter" (2026,
  arXiv:2605.19537) — backend choice alone shifts scores up to **16.6 pts**. ⇒ pin the
  provider **AND** report run-to-run variance over n>1 (this is exactly why Claim 2's
  pass^k matters — the two controls are complementary).

---

## Net verdict

The methodology is **well-founded and matches current practice**, with three honest
adjustments: (1) frame the harness as a *large but bounded, elicitation-dependent* axis,
not as dominating the model; (2) fix the **pass^k provenance** (Sierra/τ-bench, not
METR); (3) treat the **window-overflow protocol** as a novel, well-motivated contribution
and calibrate to the *effective* (~300–400k) not *claimed* (1M) window, scoring what
survives compaction to isolate the harness. Pinning + n>1 variance reporting together are
the fair-comparison control. Citations above are the spine of RESULTS.md.
