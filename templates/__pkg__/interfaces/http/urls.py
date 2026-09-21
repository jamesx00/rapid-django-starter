from django.urls import path

from . import {{domain}}

app_name = "{{domain}}"

urlpatterns = [
    path("{{domain}}/", {{domain}}.{{domain_singular}}_list, name="{{domain_singular}}_list"),
    path("{{domain}}/<int:pk>/", {{domain}}.{{domain_singular}}_detail, name="{{domain_singular}}_detail"),
]
