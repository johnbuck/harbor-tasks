Read `/app/incident.log`. It captures a short outage where requests began
failing with HTTP 500. Diagnose it and write `/app/diagnosis.md` containing:

1. **Root cause(s)** — explain the failure end to end:
   - the proximate error that returned 500s to clients,
   - the underlying mechanism that produced it,
   - and the contributing factor(s) that allowed it to happen.

2. **Evidence** — cite the specific log lines / values that support each part of
   your diagnosis (error messages, config values, the offending operation).

3. **Recommended fix** — a concrete change (config or code) that addresses the
   real root cause and prevents a recurrence.
