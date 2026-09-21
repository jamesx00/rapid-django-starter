# rapid-django-starter

Scaffolds a Django project in RAPID's horizontal layout: `data/` (only model-holding app), `readers/`, `actions/`, `interfaces/http/`, `interfaces/management_commands/`. Function-based views only.

Stdlib-only script; needs `uv` for the sync/check steps.

```
python new_rapid_project.py <name> [--dir PARENT] [--domain notes]
```

Runs `uv add django` and `django-admin startproject config .` so `config/` and `manage.py` match the installed Django version, then patches `INSTALLED_APPS` and the root `urls.py` for RAPID. Adds one sample domain (model/admin/reader/action/views/urls), ADR 0001 and a `CLAUDE.md` architecture blurb, then runs `makemigrations` and `check`.
