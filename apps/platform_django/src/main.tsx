import { StrictMode } from 'react';

import { createRoot } from 'react-dom/client';

import { initSentry } from '@/features/monitoring';

import App from './App';
import './index.css';
// Imported for its side effect: it attaches the CSRF header to the generated
// API client. Imports are evaluated before the render below, and no query fires
// until something renders, so the interceptor is in place before the first
// request.
import './services/client-config';

// Before the render, so an error thrown while the tree first mounts is still
// reported. React rethrows what no error boundary catches, and Sentry's global
// handlers are what pick it up from there.
initSentry();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
