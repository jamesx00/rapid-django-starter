"""Read-only business logic for {{domain}}. No writes, no HTTP."""

from {{pkg}}.data.models import {{Model}}


def list_{{domain}}():
    return {{Model}}.objects.order_by("-created_at")


def get_{{domain_singular}}(pk: int) -> {{Model}}:
    return {{Model}}.objects.get(pk=pk)
