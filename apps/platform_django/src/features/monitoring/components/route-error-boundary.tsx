import { useEffect } from 'react';

import * as Sentry from '@sentry/react';
import { useRouteError } from 'react-router';

/**
 * Reports what React Router swallows.
 *
 * Sentry's global handlers only see errors that reach `window`. React Router
 * catches anything a route throws and renders a boundary instead, so a render
 * error is *handled* — it never reaches the handlers, and without this it is
 * reported nowhere. That covers the application's whole render surface, which
 * is most of what can throw.
 *
 * Everything the boundary receives is captured, route error responses
 * included. The router sits behind `ProtectedRoute`, so a 404 here is a signed
 * -in user following a link this application generated, not a bot guessing
 * URLs. If that stops holding and Sentry fills with 404s, filter them with
 * `isRouteErrorResponse` from react-router.
 */
export function RouteErrorBoundary() {
  const error = useRouteError();

  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  // Deliberately unstyled: a downstream project inherits this markup and the
  // template has no business baking a look into it.
  return (
    <div role="alert">
      <h1>Something went wrong</h1>
      <p>Reload the page to try again.</p>
    </div>
  );
}
