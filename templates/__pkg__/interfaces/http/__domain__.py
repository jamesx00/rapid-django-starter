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
