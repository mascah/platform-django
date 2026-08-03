"""Write operations for the users module.

A service owns a mutation. Views, serializers and tasks call one; none of them
performs the write itself. That is what makes a change reachable from one place
and what the ``users-internal-layers`` import contract enforces.
"""

from platform_django.users.models import User


def user_update_profile(*, user_id: int, name: str | None = None) -> User:
    """Update a user's own profile and return the saved user.

    ``name`` is optional because PATCH may supply nothing to change; ``None``
    leaves the current value alone. An empty string is a value — it clears the
    field.

    Profile is deliberately narrow. Email and username are identity, owned by
    allauth, and are read-only on the API — see the serializer.
    """
    user = User.objects.get(id=user_id)

    if name is not None:
        user.name = name
        user.save(update_fields=["name"])

    return user
