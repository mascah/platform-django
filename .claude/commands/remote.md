---
description: Serve this worktree and print the SSH forward for viewing it from another machine
---

Make this worktree viewable in a browser on another machine.

1. `just ports` — this worktree's Django and Vite ports.
2. `lsof -ti :<port>` for each. Start only what is not already listening, in the
   background: `just serve` for Django, `pnpm dev` for Vite. Django needs
   `just up` first if the backing services are down.
3. `just remote` — give the user its output verbatim, in a copyable block.

The forward has to land on the same port numbers at the far end: ALLOWED_HOSTS,
the development CSP and the script tag django-vite writes into the page are all
pinned to `localhost:<port>`. If `just remote` prints the wrong host name, the
fix is `SSH_HOST` in `.env`, not a different forward.
