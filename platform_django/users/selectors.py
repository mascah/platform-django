"""Read operations for the users module.

A selector answers a question. It queries, applies access scope, and returns —
no writes, no externally visible side effects. Every read path a view serves
should route through one, so that "who may see this?" is answered in one place
rather than re-derived per endpoint.
"""

from django.db.models import QuerySet

from platform_django.users.models import User


def user_list_visible_to(viewer_id: int) -> QuerySet[User]:
    """The users ``viewer_id`` is allowed to read.

    A user may read only their own record. This is the access scope every
    user-facing read is built on; widening it is a change to this function,
    not to a caller.
    """
    return User.objects.filter(id=viewer_id).order_by("id")
