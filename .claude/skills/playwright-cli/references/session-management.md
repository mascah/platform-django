# Browser Session Management

Run multiple isolated browser sessions concurrently with state persistence.

## Named Browser Sessions

Use `-s` flag to isolate browser contexts:

```bash
# Browser 1: Authentication flow
pnpm playwright-cli -s=auth open https://app.example.com/login

# Browser 2: Public browsing (separate cookies, storage)
pnpm playwright-cli -s=public open https://example.com

# Commands are isolated by browser session
pnpm playwright-cli -s=auth fill e1 "user@example.com"
pnpm playwright-cli -s=public snapshot
```

## Browser Session Isolation Properties

Each browser session has independent:
- Cookies
- LocalStorage / SessionStorage
- IndexedDB
- Cache
- Browsing history
- Open tabs

## Browser Session Commands

```bash
# List all browser sessions
pnpm playwright-cli list

# Stop a browser session (close the browser)
pnpm playwright-cli close                # stop the default browser
pnpm playwright-cli -s=mysession close   # stop a named browser

# Stop all browser sessions
pnpm playwright-cli close-all

# Forcefully kill all daemon processes (for stale/zombie processes)
pnpm playwright-cli kill-all

# Delete browser session user data (profile directory)
pnpm playwright-cli delete-data                # delete default browser data
pnpm playwright-cli -s=mysession delete-data   # delete named browser data
```

## Environment Variable

Set a default browser session name via environment variable:

```bash
export PLAYWRIGHT_CLI_SESSION="mysession"
pnpm playwright-cli open example.com  # Uses "mysession" automatically
```

## Common Patterns

### Concurrent Scraping

```bash
#!/bin/bash
# Scrape multiple sites concurrently

# Start all browsers
pnpm playwright-cli -s=site1 open https://site1.com &
pnpm playwright-cli -s=site2 open https://site2.com &
pnpm playwright-cli -s=site3 open https://site3.com &
wait

# Take snapshots from each
pnpm playwright-cli -s=site1 snapshot
pnpm playwright-cli -s=site2 snapshot
pnpm playwright-cli -s=site3 snapshot

# Cleanup
pnpm playwright-cli close-all
```

### A/B Testing Sessions

```bash
# Test different user experiences
pnpm playwright-cli -s=variant-a open "https://app.com?variant=a"
pnpm playwright-cli -s=variant-b open "https://app.com?variant=b"

# Compare
pnpm playwright-cli -s=variant-a screenshot
pnpm playwright-cli -s=variant-b screenshot
```

### Persistent Profile

By default, browser profile is kept in memory only. Use `--persistent` flag on `open` to persist the browser profile to disk:

```bash
# Use persistent profile (auto-generated location)
pnpm playwright-cli open https://example.com --persistent

# Use persistent profile with custom directory
pnpm playwright-cli open https://example.com --profile=/path/to/profile
```

## Default Browser Session

When `-s` is omitted, commands use the default browser session:

```bash
# These use the same default browser session
pnpm playwright-cli open https://example.com
pnpm playwright-cli snapshot
pnpm playwright-cli close  # Stops default browser
```

## Browser Session Configuration

Configure a browser session with specific settings when opening:

```bash
# Open with config file
pnpm playwright-cli open https://example.com --config=.playwright/my-cli.json

# Open with specific browser
pnpm playwright-cli open https://example.com --browser=firefox

# Open in headed mode
pnpm playwright-cli open https://example.com --headed

# Open with persistent profile
pnpm playwright-cli open https://example.com --persistent
```

## Best Practices

### 1. Name Browser Sessions Semantically

```bash
# GOOD: Clear purpose
pnpm playwright-cli -s=github-auth open https://github.com
pnpm playwright-cli -s=docs-scrape open https://docs.example.com

# AVOID: Generic names
pnpm playwright-cli -s=s1 open https://github.com
```

### 2. Always Clean Up

```bash
# Stop browsers when done
pnpm playwright-cli -s=auth close
pnpm playwright-cli -s=scrape close

# Or stop all at once
pnpm playwright-cli close-all

# If browsers become unresponsive or zombie processes remain
pnpm playwright-cli kill-all
```

### 3. Delete Stale Browser Data

```bash
# Remove old browser data to free disk space
pnpm playwright-cli -s=oldsession delete-data
```
