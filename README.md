# rapid-django-starter

Scaffolds a Django project in RAPID's horizontal layout: `data/` (only model-holding app), `readers/`, `actions/`, `interfaces/http/`, `interfaces/management_commands/`. Function-based views only.

Stdlib-only script; needs `uv` for the sync/check steps.

```
python new_rapid_project.py <name> [--dir PARENT] [--domain notes] [--no-sync]
```

Generates config, one sample domain (model/admin/reader/action/views/urls), ADR 0001 and a `CLAUDE.md` architecture blurb, then runs `uv sync`, `makemigrations` and `check`.
