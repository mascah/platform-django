"""Write operations for the users module.

A service owns a mutation. Views, serializers and tasks call one; none of them
performs the write itself. That is what makes a change reachable from one place
and what the ``users-internal-layers`` import contract enforces.
"""

from platform_django.users.models import User


def user_update_profile(
    *,
    user_id: int,
    name: str | None = None,
    username: str | None = None,
    email: str | None = None,
) -> User:
    """Update a user's own profile fields and return the saved user.

    Only the fields passed are written; anything left as ``None`` keeps its
    current value. An empty string is a value — it clears the field.
    """
    user = User.objects.get(id=user_id)

    updates = {"name": name, "username": username, "email": email}
    changed = [field for field, value in updates.items() if value is not None]
    for field in changed:
        setattr(user, field, updates[field])

    if changed:
        user.save(update_fields=changed)

    return user
