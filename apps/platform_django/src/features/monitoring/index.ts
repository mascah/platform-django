import * as Sentry from '@sentry/react';

export { RouteErrorBoundary } from './components/route-error-boundary';

/**
 * Browser error reporting, off unless a public DSN is set.
 *
 * `VITE_SENTRY_DSN` is not `SENTRY_DSN`. The server DSN belongs to the server
 * project and never leaves the dyno; this one ships inside the JavaScript
 * bundle and is public by design, which is what the `VITE_` prefix already
 * signals for the PostHog key next to it. They are separate Sentry projects.
 *
 * Unset means off, quietly and with nothing logged — the same gate
 * `sentry_sdk.init` and the PostHog init are already behind.
 *
 */
export function initSentry() {
  const dsn = import.meta.env.VITE_SENTRY_DSN;

  // Only in a production build: a dev server reports every hot reload error
  // and every React StrictMode double-invocation as a real one.
  if (!dsn || !import.meta.env.PROD) return;

  Sentry.init({
    dsn,
    // Without this a Preview reports into production issues (ADR-0011). It
    // mirrors the server's SENTRY_ENVIRONMENT and defaults the same way.
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || 'production',
    // Errors only. Tracing and Session Replay are neither default integrations
    // nor asked for, and they are where a browser bundle gets heavy.
    //
    // The release is not set here: @sentry/vite-plugin injects it at build
    // time, alongside the source maps that make the trace worth reading, and
    // both are absent together when no auth token is configured.
  });
}
