from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from platform_django.users.selectors import user_list_visible_to
from platform_django.users.services import user_update_profile

from .serializers import UserSerializer


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    """Orchestration only: reads call the selector, writes call the service."""

    serializer_class = UserSerializer
    lookup_field = "username"
    # The router's default value regex is "[^/.]+", which excludes the dot that
    # Django's own UnicodeUsernameValidator allows. A username like
    # "ada@example.com" - what createsuperuser gets when an email is typed at
    # the username prompt - then has no reversible detail URL, and the "url"
    # field in UserSerializer raises ImproperlyConfigured on every response
    # that serializes that user, /api/users/me/ included. Anything the
    # validator accepts has to be routable; only "/" is off limits.
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        assert isinstance(self.request.user.id, int)
        return user_list_visible_to(self.request.user.id)

    def perform_update(self, serializer):
        # validated_data carries exactly the writable serializer fields this
        # request supplied, which are the profile fields the service accepts.
        # That the two agree is asserted in tests/api/test_serializers.py —
        # this serializer is a ModelSerializer, so its field list answers to
        # the model, not to the service signature.
        serializer.instance = user_update_profile(
            user_id=serializer.instance.pk,
            **serializer.validated_data,
        )

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)
