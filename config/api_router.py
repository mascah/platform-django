from django.conf import settings
from rest_framework.routers import DefaultRouter
from rest_framework.routers import SimpleRouter

from platform_django.users.api.views import UserViewSet

router = DefaultRouter() if settings.DEBUG else SimpleRouter()

# basename is explicit: the viewset builds its queryset from a selector rather
# than declaring a class-level `queryset`, so the router has nothing to infer
# the route names from.
router.register("users", UserViewSet, basename="user")


app_name = "api"
urlpatterns = router.urls
