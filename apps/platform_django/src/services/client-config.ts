import { client } from './platform_django/client.gen';

// Configuration for the generated API client, applied once at startup by the
// side-effect import in main.tsx. Template-owned: every feature's queries go
// through this client, so nothing here belongs to a particular feature.
//
// No base URL is set. Django serves this bundle in both environments — in
// development django-vite only points the script tags at the Vite server, so
// the page origin is Django's either way — and the generated client resolves a
// relative path against that origin already. Naming the origin explicitly would
// pin a host the page was not necessarily loaded on, which turns a same-origin
// request into a cross-origin one that carries no cookies and fails the
// `connect-src 'self'` policy in config/settings/local.py.

// The methods Django's CsrfViewMiddleware exempts.
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS', 'TRACE']);

// config/settings/base.py sets CSRF_COOKIE_HTTPONLY = True, so JavaScript
// cannot read the csrftoken cookie; the meta tag rendered by
// platform_django/templates/apps/platform_django.html is the route, and it
// carries the value the cookie carries.
//
// Without this header DRF's SessionAuthentication rejects every unsafe request
// from a signed-in user. An anonymous one passes without it, so the failure
// appears only after someone signs in — hence the noisy warning rather than a
// silent no-op, which is how this went unnoticed before.
client.interceptors.request.use((request) => {
  if (SAFE_METHODS.has(request.method.toUpperCase())) {
    return request;
  }
  const token = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute('content');
  if (token) {
    request.headers.set('X-CSRFToken', token);
  } else {
    console.warn(
      'No csrf-token meta tag: this request will be rejected once signed in.',
    );
  }
  return request;
});
