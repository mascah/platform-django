from pathlib import Path

from csp.decorators import csp_exempt
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.http import HttpResponse
from django.urls import include
from django.urls import path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView
from drf_spectacular.views import SpectacularSwaggerView
from rest_framework.permissions import AllowAny


def healthz(request):
    """Health check endpoint for load balancer."""
    return HttpResponse("ok", content_type="text/plain")


def serve_landing_page(request):
    """Serve pre-rendered Astro landing page."""
    if settings.DEBUG:
        # In development, read from the Astro build output directly
        html_path = Path(settings.BASE_DIR) / "apps/landing/dist/index.html"
    else:
        # In production, read from STATIC_ROOT (populated by collectstatic)
        html_path = Path(settings.STATIC_ROOT) / "index.html"

    if html_path.exists():
        return FileResponse(html_path.open("rb"), content_type="text/html")
    msg = "Landing page not found. Run 'pnpm build' in apps/landing first."
    raise Http404(msg)


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("", serve_landing_page, name="home"),
    path(
        "app/",
        login_required(TemplateView.as_view(template_name="apps/platform_django.html")),
        name="app",
    ),
    path(
        "app/<path:path>",
        login_required(TemplateView.as_view(template_name="apps/platform_django.html")),
        name="app-catchall",
    ),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("platform_django.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
]

if settings.DEBUG:
    # Allow unauthenticated access to the API schema for openapi client generation
    urlpatterns += [
        path(
            "api/schema/",
            csp_exempt()(SpectacularAPIView.as_view(permission_classes=[AllowAny])),
            name="api-schema",
        ),
        path(
            "api/docs/",
            csp_exempt()(
                SpectacularSwaggerView.as_view(
                    url_name="api-schema", permission_classes=[AllowAny]
                )
            ),
            name="api-docs",
        ),
    ]
else:
    urlpatterns += [
        path(
            "api/schema/",
            csp_exempt()(SpectacularAPIView.as_view()),
            name="api-schema",
        ),
        path(
            "api/docs/",
            csp_exempt()(SpectacularSwaggerView.as_view(url_name="api-schema")),
            name="api-docs",
        ),
    ]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls)),
            *urlpatterns,
        ]
