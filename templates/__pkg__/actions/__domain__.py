"""State-changing business logic for {{domain}}. Interfaces call these rather than
constructing/saving models inline."""

from {{pkg}}.data.models import {{Model}}


def create_{{domain_singular}}(*, title: str, body: str = "") -> {{Model}}:
    return {{Model}}.objects.create(title=title, body=body)
