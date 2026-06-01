Read `/app/incident.log`. It captures a short outage where requests began
failing with HTTP 500. The incident has **more than one contributing cause**,
and the log also contains some **unrelated noise** that did NOT cause the
outage. Diagnose it carefully and write `/app/diagnosis.md` containing:

1. **Root cause(s)** — explain the failure end to end:
   - the proximate error that returned 500s to clients,
   - the underlying mechanism that produced it,
   - and the contributing factor(s) that allowed it to happen.
   Cover *all* of the genuine contributing causes, not just the first one you
   spot.

2. **Evidence** — cite the specific log lines / values that support each part of
   your diagnosis (error messages, config values, the offending operation).

3. **Red herring** — call out any log entries that look alarming but are
   actually unrelated to the crash, and say why they are not the cause.

4. **Recommended fix** — a concrete change (config or code) that addresses the
   real root cause and prevents a recurrence.

Your diagnosis is graded on how many of the genuine root-cause and evidence
points you correctly identify (and whether you avoid blaming the red herring) —
a shallow, single-cause diagnosis scores only a fraction.
