import inspect

from platform_django.users.api.serializers import UserSerializer
from platform_django.users.services import user_update_profile


def test_writable_fields_match_the_service_signature():
    """The viewset splats validated_data into the service, so these must agree.

    Without this, adding a writable field to the serializer passes CI and
    raises TypeError on the first request that supplies it. Widen the service
    to accept the new field, or mark the field read_only.
    """
    writable = {
        name for name, field in UserSerializer().fields.items() if not field.read_only
    }
    accepted = set(inspect.signature(user_update_profile).parameters) - {"user_id"}

    assert writable == accepted
