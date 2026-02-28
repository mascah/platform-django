from django import template
from django.utils.safestring import mark_safe
from django_vite.core.asset_loader import DjangoViteAssetLoader

register = template.Library()


@register.simple_tag(takes_context=True)
@mark_safe  # noqa: S308
def vite_react_refresh_csp(context, app="default"):
    """
    vite_react_refresh with automatic CSP nonce injection.

    This is a workaround for django-vite's template tags not properly
    resolving Django template variables passed as kwargs.
    See: https://github.com/MrBin99/django-vite/pull/120
    """
    request = context.get("request")
    # Must call str() to trigger django-csp's lazy nonce generation
    # and register it for inclusion in the CSP header
    nonce = (
        str(request.csp_nonce) if request and hasattr(request, "csp_nonce") else None
    )
    kwargs = {"nonce": nonce} if nonce else {}
    return DjangoViteAssetLoader.instance().generate_vite_react_refresh_url(
        app, **kwargs
    )
