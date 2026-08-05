import { expect, test } from '@/fixtures';

// Browser error reporting is the one integration that fails silently in both
// directions: a missing connect-src entry blocks the request in the renderer
// before anything is logged, and a DSN that never reaches the bundle looks
// identical from the outside. Neither shows up in a build or a typecheck, so
// the only evidence that works is a browser actually making the request.
//
// The DSN is read from the environment rather than hardcoded because it has to
// be the same one the bundle was built with — a production build and CI set it
// together. Locally, /app/ is served by the Vite dev server, where the init is
// gated off by import.meta.env.PROD, so there is nothing to assert.
const dsn = process.env.VITE_SENTRY_DSN;
// Mirrors the default in the init itself, so a DSN configured without an
// environment asserts what the SDK actually sends rather than "undefined".
const environment = process.env.VITE_SENTRY_ENVIRONMENT || 'production';

test.describe('Sentry browser reporting', () => {
  test.skip(!dsn, 'needs a production build of the app with VITE_SENTRY_DSN set at build time');

  test('an uncaught error reaches the ingestion host', async ({ page }) => {
    const ingestionHost = new URL(dsn!).host;

    // Fulfilled rather than passed through: the assertion is that the browser
    // issued the request, and CI has no Sentry account to send it to. Routing
    // intercepts before the request leaves the renderer, but *after* CSP has
    // had its say, so a policy missing the host fails here rather than passing
    // quietly.
    const envelope = page.waitForRequest(
      (request) => new URL(request.url()).host === ingestionHost,
    );
    await page.route(`**://${ingestionHost}/**`, (route) =>
      route.fulfill({ status: 200, body: '{}' }),
    );

    await page.goto('/app/');
    await expect(page.locator('#root')).not.toBeEmpty();

    // Thrown from a timer so it surfaces as an uncaught error on window rather
    // than as the return value of the evaluate call, which Playwright catches.
    await page.evaluate(() => {
      setTimeout(() => {
        throw new Error('e2e sentry probe');
      });
    });

    const request = await envelope;
    expect(request.url()).toContain('/envelope/');

    const body = request.postData();
    expect(body).toContain('e2e sentry probe');
    // The environment tag is what keeps a Preview's errors out of production
    // issues (ADR-0011), and CI builds with a value that is neither.
    expect(body).toContain(`"environment":"${environment}"`);
  });

  // The case above only proves the transport. React Router catches whatever a
  // route throws and renders a boundary, so a render error is handled and
  // never reaches the global handlers that case relies on — the application's
  // whole render surface reported nothing until RouteErrorBoundary did it.
  //
  // A URL matching no route reaches that same boundary without the template
  // having to ship a component that throws on purpose.
  test('an error React Router handles is reported too', async ({ page }) => {
    const ingestionHost = new URL(dsn!).host;

    const envelope = page.waitForRequest(
      (request) => new URL(request.url()).host === ingestionHost,
    );
    await page.route(`**://${ingestionHost}/**`, (route) =>
      route.fulfill({ status: 200, body: '{}' }),
    );

    await page.goto('/app/no-such-route');
    await expect(page.getByRole('alert')).toBeVisible();

    expect((await envelope).postData()).toBeTruthy();
  });
});
