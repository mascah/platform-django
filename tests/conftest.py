"""Keep the template's own tooling tests out of a project made from it.

``bin/eject`` and ``bin/worktree-create`` belong to the template rather than to
anything a project built on it ships, and driving them as subprocesses is most
of a run's wall clock. A clone keeps the files so changes still merge in both
directions (ADR-0006) and simply stops collecting them, on the same datum that
already distinguishes one project from another: the slug.

The rest of this directory stays collected everywhere — settings, logging,
connection URLs and project identity are what a clone inherits and owns.
"""

from django.conf import settings

TEMPLATE_SLUG = "platform_django"

TOOLING = ["test_eject.py", "test_worktree_create.py"]

collect_ignore = [] if settings.PROJECT_SLUG == TEMPLATE_SLUG else TOOLING
