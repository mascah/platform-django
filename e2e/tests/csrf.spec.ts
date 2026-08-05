import { expect, test } from '@/fixtures';

// The chain src/services/client-config.ts depends on, end to end: the shell
// renders a token where the interceptor's selector looks, and that token is the
// one Django accepts under the header name the interceptor sets.
//
// It is asserted here rather than in pytest because rendering the shell needs a
// built manifest, which only this job has. It is worth asserting at all because
// the previous version failed silently: CSRF_COOKIE_HTTPONLY makes the cookie
// unreadable, and DRF only enforces CSRF once a request is authenticated, so a
// broken token source leaves anonymous reads working and breaks writes for
// signed-in users alone.
test.describe('CSRF', () => {
  test('a signed-in write is accepted with the shell token and rejected without', async ({
    page,
  }) => {
    await page.goto('/app/');
    // The interceptor's own expression, so a selector that stops matching
    // fails here rather than waiting for a locator that will never resolve.
    const token = await page.evaluate(
      () => document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ?? null,
    );
    expect(token).toBeTruthy();

    const me = await page.request.get('/api/users/me/');
    expect(me.status()).toBe(200);
    const { username } = await me.json();
    const url = `/api/users/${encodeURIComponent(username)}/`;

    const withoutToken = await page.request.fetch(url, {
      method: 'PATCH',
      data: { name: 'Rejected' },
    });
    expect(withoutToken.status()).toBe(403);

    const withToken = await page.request.fetch(url, {
      method: 'PATCH',
      headers: { 'X-CSRFToken': token! },
      data: { name: 'Accepted' },
    });
    expect(withToken.status()).toBe(200);
  });
});
