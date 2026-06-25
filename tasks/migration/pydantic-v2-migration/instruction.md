`/app/settings.py` was written for **Pydantic v1** but the installed Pydantic is
**v2**. Several distinct v1 APIs in the file are breaking changes under v2.
Migrate the whole module (and add `pydantic-settings`) so that:

```
cd /app && python -m pytest tests/test_settings.py
```

passes — every test.

Constraints:

- You may install packages (you have internet access).
- Do not modify the test file (`/app/tests/test_settings.py`).
- Keep the field **names** and **default values** in `AppSettings` unchanged,
  and preserve the module's existing behavior (its validators, settings config,
  and serialization helpers must keep working as before).
