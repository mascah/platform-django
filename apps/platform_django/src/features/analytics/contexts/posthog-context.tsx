import { type ReactNode, useEffect } from 'react';

import posthog from 'posthog-js';

interface PostHogProviderProps {
  children: ReactNode;
}

export function PostHogProvider({ children }: PostHogProviderProps) {
  useEffect(() => {
    // Only initialize PostHog in production
    const posthogKey = import.meta.env.VITE_POSTHOG_KEY;
    // app.posthog.com is the UI, not an ingestion endpoint, and it is absent
    // from connect-src — the old default was blocked by CSP the moment a key
    // was set. This one matches the policy and the landing page's default.
    const posthogHost = import.meta.env.VITE_POSTHOG_HOST || 'https://us.i.posthog.com';

    if (posthogKey && import.meta.env.PROD) {
      posthog.init(posthogKey, {
        api_host: posthogHost,
        capture_pageview: true,
        capture_pageleave: true,
      });
    }
  }, []);

  return <>{children}</>;
}
