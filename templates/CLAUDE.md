## Architecture

RAPID layering, horizontal by concern - no per-domain Django apps. One `{{pkg}}` package
with `data/` (the only model-holding app), `readers/`, `actions/`, and `interfaces/http/` +
`interfaces/management_commands/` (the other registered app). Function-based views only,
never class-based. See `docs/adr/0001-rapid-layering-and-function-based-views.md`.
