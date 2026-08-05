// Stamps the session hint on <html> before first paint, so the landing page
// shows the right call to action without a flash. Not authentication: it picks
// a label and nothing else. See config/middleware.py.
document.documentElement.classList.add(
  /(?:^|; )session_hint=1(?:;|$)/.test(document.cookie) ? 'signed-in' : 'signed-out',
);
