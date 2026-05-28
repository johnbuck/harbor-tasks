`/app/settings.py` fails to import under the installed version of Pydantic.
Migrate it so that:

```
cd /app && python -m pytest tests/test_settings.py
```

passes.

Constraints:

- You may install packages (you have internet access).
- Do not modify the test file (`/app/tests/test_settings.py`).
- Keep the field names and default values in `AppSettings` unchanged.
