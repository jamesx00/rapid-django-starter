#!/usr/bin/env python3
"""Scaffold a Django project using RAPID's horizontal layout.

    python new_rapid_project.py <name> [--dir PARENT] [--domain NOTE_DOMAIN] [--no-sync]

Layout (see docs/adr/0001 in the generated project):

    <name>/
      config/                  settings, urls, wsgi/asgi
      <name>/data/             only model-holding app (models/, admin.py, migrations/)
      <name>/readers/          read-only business logic, one file per domain
      <name>/actions/          state-changing business logic, one file per domain
      <name>/interfaces/http/  thin function-based views + urls
      <name>/interfaces/management_commands/   registered only for command discovery

Stdlib only. Requires `uv` on PATH for the sync/check steps (skip with --no-sync).
"""

import argparse
import re
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

DJANGO_MIN = "5.2"


def render(text: str, ctx: dict[str, str]) -> str:
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", value)
    return text


# --------------------------------------------------------------------------- templates
# Paths use {{pkg}} / {{domain}} placeholders too; both are substituted before writing.

FILES: dict[str, str] = {
    "manage.py": '''\
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
''',
    ".gitignore": """\
__pycache__/
*.py[cod]
.venv/
db.sqlite3
.env
""",
    "pyproject.toml": """\
[project]
name = "{{name}}"
version = "0.1.0"
description = ""
requires-python = ">=3.12"
dependencies = [
    "django>={{django_min}}",
]
""",
    "config/__init__.py": "",
    "config/settings.py": '''\
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-{{secret}}"
DEBUG = True
ALLOWED_HOSTS = []

# RAPID: only these two project apps are registered. readers/, actions/ and
# interfaces/http/ are plain Python packages, imported directly.
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "{{pkg}}.data",
    "{{pkg}}.interfaces.management_commands",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
''',
    "config/urls.py": '''\
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("{{pkg}}.interfaces.http.urls")),
]
''',
    "config/wsgi.py": '''\
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_wsgi_application()
''',
    "config/asgi.py": '''\
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
application = get_asgi_application()
''',
    # ---- package
    "{{pkg}}/__init__.py": "",
    # data: the only model-holding app
    "{{pkg}}/data/__init__.py": "",
    "{{pkg}}/data/apps.py": '''\
from django.apps import AppConfig


class DataConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "{{pkg}}.data"
    label = "data"
''',
    "{{pkg}}/data/models/__init__.py": '''\
from .{{domain_singular}} import {{Model}}

__all__ = ["{{Model}}"]
''',
    "{{pkg}}/data/models/{{domain_singular}}.py": '''\
from django.db import models


class {{Model}}(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
''',
    "{{pkg}}/data/admin.py": '''\
from django.contrib import admin

from .models import {{Model}}

admin.site.register({{Model}})
''',
    "{{pkg}}/data/migrations/__init__.py": "",
    # readers / actions: plain Python, not Django apps
    "{{pkg}}/readers/__init__.py": "",
    "{{pkg}}/readers/{{domain}}.py": '''\
"""Read-only business logic for {{domain}}. No writes, no HTTP."""

from {{pkg}}.data.models import {{Model}}


def list_{{domain}}():
    return {{Model}}.objects.order_by("-created_at")


def get_{{domain_singular}}(pk: int) -> {{Model}}:
    return {{Model}}.objects.get(pk=pk)
''',
    "{{pkg}}/actions/__init__.py": "",
    "{{pkg}}/actions/{{domain}}.py": '''\
"""State-changing business logic for {{domain}}. Interfaces call these rather than
constructing/saving models inline."""

from {{pkg}}.data.models import {{Model}}


def create_{{domain_singular}}(*, title: str, body: str = "") -> {{Model}}:
    return {{Model}}.objects.create(title=title, body=body)
''',
    # interfaces
    "{{pkg}}/interfaces/__init__.py": "",
    "{{pkg}}/interfaces/http/__init__.py": "",
    "{{pkg}}/interfaces/http/{{domain}}.py": '''\
"""Thin function-based views. No business logic here: call readers/actions."""

from django.http import Http404, JsonResponse

from {{pkg}}.data.models import {{Model}}
from {{pkg}}.readers import {{domain}} as readers


def {{domain_singular}}_list(request):
    items = [{"id": n.pk, "title": n.title} for n in readers.list_{{domain}}()]
    return JsonResponse({"{{domain}}": items})


def {{domain_singular}}_detail(request, pk):
    try:
        item = readers.get_{{domain_singular}}(pk)
    except {{Model}}.DoesNotExist:
        raise Http404
    return JsonResponse({"id": item.pk, "title": item.title, "body": item.body})
''',
    "{{pkg}}/interfaces/http/urls.py": '''\
from django.urls import path

from . import {{domain}}

app_name = "{{domain}}"

urlpatterns = [
    path("{{domain}}/", {{domain}}.{{domain_singular}}_list, name="{{domain_singular}}_list"),
    path("{{domain}}/<int:pk>/", {{domain}}.{{domain_singular}}_detail, name="{{domain_singular}}_detail"),
]
''',
    "{{pkg}}/interfaces/management_commands/__init__.py": "",
    "{{pkg}}/interfaces/management_commands/apps.py": '''\
from django.apps import AppConfig


class ManagementCommandsConfig(AppConfig):
    name = "{{pkg}}.interfaces.management_commands"
    label = "management_commands"
''',
    "{{pkg}}/interfaces/management_commands/management/__init__.py": "",
    "{{pkg}}/interfaces/management_commands/management/commands/__init__.py": "",
    # docs
    "docs/adr/0001-rapid-layering-and-function-based-views.md": """\
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
""",
    "CLAUDE.md": """\
## Architecture

RAPID layering, horizontal by concern - no per-domain Django apps. One `{{pkg}}` package
with `data/` (the only model-holding app), `readers/`, `actions/`, and `interfaces/http/` +
`interfaces/management_commands/` (the other registered app). Function-based views only,
never class-based. See `docs/adr/0001-rapid-layering-and-function-based-views.md`.
""",
}


def to_identifier(name: str) -> str:
    ident = re.sub(r"[^0-9a-zA-Z_]", "_", name).strip("_").lower()
    if not ident or ident[0].isdigit():
        sys.exit(f"error: '{name}' cannot be made into a valid Python package name")
    return ident


def singular(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 1 else word


def run(cmd: list[str], cwd: Path) -> None:
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", help="project name (also used, snake_cased, as the top-level package)")
    p.add_argument("--dir", default=".", help="parent directory (default: cwd)")
    p.add_argument("--domain", default="notes", help="sample domain, plural (default: notes)")
    p.add_argument("--no-sync", action="store_true", help="only write files; skip uv sync / makemigrations / check")
    args = p.parse_args()

    pkg = to_identifier(args.name)
    domain = to_identifier(args.domain)
    domain_singular = singular(domain)
    ctx = {
        "name": args.name,
        "pkg": pkg,
        "domain": domain,
        "domain_singular": domain_singular,
        "Model": "".join(part.capitalize() for part in domain_singular.split("_")),
        "django_min": DJANGO_MIN,
        "secret": secrets.token_urlsafe(50),
    }

    root = Path(args.dir).expanduser().resolve() / args.name
    if root.exists():
        sys.exit(f"error: {root} already exists")

    for rel, content in FILES.items():
        path = root / render(rel, ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(content, ctx))
    print(f"wrote {len(FILES)} files to {root}")

    if args.no_sync:
        return
    if not shutil.which("uv"):
        sys.exit("uv not found on PATH; re-run with --no-sync or install uv")
    run(["uv", "sync"], root)
    run(["uv", "run", "python", "manage.py", "makemigrations", "data"], root)
    run(["uv", "run", "python", "manage.py", "check"], root)
    print(f"\ndone. cd {root} && uv run python manage.py migrate && uv run python manage.py runserver")


if __name__ == "__main__":
    main()
