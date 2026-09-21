# 0001. RAPID layering, function-based views only

## Status

Accepted

## Decision

Structure the project horizontally by concern, not vertically by domain. There is no
per-domain Django app. One top-level `{{pkg}}` package holds:

- `{{pkg}}/data/` - the only model-holding Django app. One model per file under
  `data/models/`, re-exported from `data/models/__init__.py`. `admin.py` lives here too.
- `{{pkg}}/readers/` - plain Python. Read-only business logic, one file per domain.
- `{{pkg}}/actions/` - plain Python. State-changing business logic, one file per domain.
- `{{pkg}}/interfaces/http/` - thin views only, one file per domain, plus `urls.py`.
- `{{pkg}}/interfaces/management_commands/` - the other registered Django app, solely so
  command discovery finds `management/commands/*.py`.

Only `{{pkg}}.data` and `{{pkg}}.interfaces.management_commands` are in `INSTALLED_APPS`.

Views are function-based only, never class-based. Preconditions use decorators, not mixins.
Shared behavior is composed via helper functions, not inheritance.

## Consequences

- A new domain concept gets a new file in `readers/`, `actions/`, `interfaces/http/` and
  `data/models/` - never a new Django app.
- Tests target `readers/` and `actions/` directly; views have no independent logic.
