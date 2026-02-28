Authentication
==============

Overview
--------

The project uses `django-allauth <https://docs.allauth.org/>`_ for authentication with session-based authentication for both the web UI and the API layer.

- **Web UI**: django-allauth provides pages for login, signup, password reset, and email verification.
- **API**: Django REST Framework uses session authentication via cookies. Users log in through allauth, and the session cookie authenticates subsequent API requests.

Authentication Flow
-------------------

Web UI
^^^^^^

django-allauth serves authentication pages under ``/accounts/``:

- ``/accounts/login/`` — Login page
- ``/accounts/signup/`` — Registration page
- ``/accounts/password/reset/`` — Password reset
- ``/accounts/confirm-email/`` — Email verification

When a user visits a protected page without being authenticated, they are redirected to the allauth login page. After successful login, they are redirected back to the originally requested page.

API
^^^

API endpoints use session authentication via the session cookie. The flow is:

1. The user logs in through the allauth login page (or programmatically).
2. Django sets a session cookie in the browser.
3. Subsequent API requests include the session cookie automatically.
4. Django REST Framework's ``SessionAuthentication`` validates the session and attaches ``request.user``.

.. code-block:: python

    # config/settings/base.py
    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework.authentication.SessionAuthentication",
        ],
    }

Configuration
-------------

Key settings that control authentication behavior:

.. code-block:: python

    # config/settings/base.py

    # Control whether new users can register
    ACCOUNT_ALLOW_SIGNUPS = env.bool("DJANGO_ACCOUNT_ALLOW_REGISTRATION", default=True)

    # django-allauth settings
    ACCOUNT_AUTHENTICATION_METHOD = "email"
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_EMAIL_VERIFICATION = "mandatory"
    ACCOUNT_UNIQUE_EMAIL = True

The ``DJANGO_ACCOUNT_ALLOW_REGISTRATION`` environment variable controls whether the signup page is available. Set it to ``False`` to disable public registration.

Custom User Model
-----------------

The custom user model lives in ``platform_django/users/``:

.. code-block:: python

    # platform_django/users/models.py
    from django.contrib.auth.models import AbstractUser

    class User(AbstractUser):
        ...

Even if the default Django user model is sufficient today, always define a custom user model at the start of a project. Changing the user model after tables exist requires a complex migration. Having a custom model in place allows future customization (adding fields, changing authentication methods) without that pain.

The custom model is registered in settings:

.. code-block:: python

    # config/settings/base.py
    AUTH_USER_MODEL = "users.User"

Protected Routes
----------------

Django Views
^^^^^^^^^^^^

Use the ``login_required`` decorator on Django views that serve the React SPA. This ensures only authenticated users can access the application:

.. code-block:: python

    from django.contrib.auth.decorators import login_required

    @login_required
    def app_view(request):
        return render(request, "app.html")

Unauthenticated users are redirected to the allauth login page.

DRF API Endpoints
^^^^^^^^^^^^^^^^^

API endpoints are protected by DRF's ``SessionAuthentication`` and permission classes:

.. code-block:: python

    from rest_framework.permissions import IsAuthenticated
    from rest_framework.views import APIView

    class TaskListView(APIView):
        permission_classes = [IsAuthenticated]

        def get(self, request):
            ...

Testing Authentication
----------------------

In view tests, use ``client.force_login()`` to authenticate without going through the login flow:

.. code-block:: python

    import pytest
    from django.test import Client

    @pytest.mark.django_db
    def test_protected_view(user):
        client = Client()
        client.force_login(user)
        response = client.get("/app/")
        assert response.status_code == 200

For DRF API tests, use ``force_authenticate()`` on the ``APIClient``:

.. code-block:: python

    import pytest
    from rest_framework.test import APIClient

    @pytest.mark.django_db
    def test_api_endpoint(user):
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get("/api/tasks/")
        assert response.status_code == 200

See Also
--------

- `django-allauth documentation <https://docs.allauth.org/>`_ — Full configuration reference
- `Django authentication <https://docs.djangoproject.com/en/stable/topics/auth/>`_ — Django's built-in auth system
- `DRF authentication <https://www.django-rest-framework.org/api-guide/authentication/>`_ — DRF authentication classes
