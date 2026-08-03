from rest_framework import serializers

from platform_django.users.models import User


class UserSerializer(serializers.ModelSerializer[User]):
    class Meta:
        model = User
        fields = ["username", "name", "url", "email", "id"]

        extra_kwargs = {
            "url": {"view_name": "api:user-detail", "lookup_field": "username"},
            # Identity, not profile. A ModelSerializer makes every listed field
            # writable by default, which let this endpoint change an address
            # without allauth ever seeing it — ACCOUNT_EMAIL_VERIFICATION is
            # "mandatory", and User.email would diverge from the EmailAddress
            # records that actually record verification. Email changes go
            # through allauth's flow at /_allauth/.
            "email": {"read_only": True},
            # Changing this changes the user's URL: it is the viewset's
            # lookup_field and the basis of User.get_absolute_url.
            "username": {"read_only": True},
        }
