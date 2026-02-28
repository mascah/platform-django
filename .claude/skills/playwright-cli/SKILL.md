---
name: playwright-cli
description: Automates browser interactions for web testing, form filling, screenshots, and data extraction. Use when the user needs to navigate websites, interact with web pages, fill forms, take screenshots, test web applications, or extract information from web pages.
allowed-tools: Bash(pnpm playwright-cli:*)
---

# Browser Automation with playwright-cli

## Quick start

```bash
# open new browser
pnpm playwright-cli open
# navigate to a page
pnpm playwright-cli goto https://playwright.dev
# interact with the page using refs from the snapshot
pnpm playwright-cli click e15
pnpm playwright-cli type "page.click"
pnpm playwright-cli press Enter
# take a screenshot (rarely used, as snapshot is more common)
pnpm playwright-cli screenshot
# close the browser
pnpm playwright-cli close
```

## Commands

### Core

```bash
pnpm playwright-cli open
# open and navigate right away
pnpm playwright-cli open https://example.com/
pnpm playwright-cli goto https://playwright.dev
pnpm playwright-cli type "search query"
pnpm playwright-cli click e3
pnpm playwright-cli dblclick e7
pnpm playwright-cli fill e5 "user@example.com"
pnpm playwright-cli drag e2 e8
pnpm playwright-cli hover e4
pnpm playwright-cli select e9 "option-value"
pnpm playwright-cli upload ./document.pdf
pnpm playwright-cli check e12
pnpm playwright-cli uncheck e12
pnpm playwright-cli snapshot
pnpm playwright-cli snapshot --filename=after-click.yaml
pnpm playwright-cli eval "document.title"
pnpm playwright-cli eval "el => el.textContent" e5
pnpm playwright-cli dialog-accept
pnpm playwright-cli dialog-accept "confirmation text"
pnpm playwright-cli dialog-dismiss
pnpm playwright-cli resize 1920 1080
pnpm playwright-cli close
```

### Navigation

```bash
pnpm playwright-cli go-back
pnpm playwright-cli go-forward
pnpm playwright-cli reload
```

### Keyboard

```bash
pnpm playwright-cli press Enter
pnpm playwright-cli press ArrowDown
pnpm playwright-cli keydown Shift
pnpm playwright-cli keyup Shift
```

### Mouse

```bash
pnpm playwright-cli mousemove 150 300
pnpm playwright-cli mousedown
pnpm playwright-cli mousedown right
pnpm playwright-cli mouseup
pnpm playwright-cli mouseup right
pnpm playwright-cli mousewheel 0 100
```

### Save as

```bash
pnpm playwright-cli screenshot
pnpm playwright-cli screenshot e5
pnpm playwright-cli screenshot --filename=page.png
pnpm playwright-cli pdf --filename=page.pdf
```

### Tabs

```bash
pnpm playwright-cli tab-list
pnpm playwright-cli tab-new
pnpm playwright-cli tab-new https://example.com/page
pnpm playwright-cli tab-close
pnpm playwright-cli tab-close 2
pnpm playwright-cli tab-select 0
```

### Storage

```bash
pnpm playwright-cli state-save
pnpm playwright-cli state-save auth.json
pnpm playwright-cli state-load auth.json

# Cookies
pnpm playwright-cli cookie-list
pnpm playwright-cli cookie-list --domain=example.com
pnpm playwright-cli cookie-get session_id
pnpm playwright-cli cookie-set session_id abc123
pnpm playwright-cli cookie-set session_id abc123 --domain=example.com --httpOnly --secure
pnpm playwright-cli cookie-delete session_id
pnpm playwright-cli cookie-clear

# LocalStorage
pnpm playwright-cli localstorage-list
pnpm playwright-cli localstorage-get theme
pnpm playwright-cli localstorage-set theme dark
pnpm playwright-cli localstorage-delete theme
pnpm playwright-cli localstorage-clear

# SessionStorage
pnpm playwright-cli sessionstorage-list
pnpm playwright-cli sessionstorage-get step
pnpm playwright-cli sessionstorage-set step 3
pnpm playwright-cli sessionstorage-delete step
pnpm playwright-cli sessionstorage-clear
```

### Network

```bash
pnpm playwright-cli route "**/*.jpg" --status=404
pnpm playwright-cli route "https://api.example.com/**" --body='{"mock": true}'
pnpm playwright-cli route-list
pnpm playwright-cli unroute "**/*.jpg"
pnpm playwright-cli unroute
```

### DevTools

```bash
pnpm playwright-cli console
pnpm playwright-cli console warning
pnpm playwright-cli network
pnpm playwright-cli run-code "async page => await page.context().grantPermissions(['geolocation'])"
pnpm playwright-cli tracing-start
pnpm playwright-cli tracing-stop
pnpm playwright-cli video-start
pnpm playwright-cli video-stop video.webm
```

## Open parameters
```bash
# Use specific browser when creating session
pnpm playwright-cli open --browser=chrome
pnpm playwright-cli open --browser=firefox
pnpm playwright-cli open --browser=webkit
pnpm playwright-cli open --browser=msedge
# Connect to browser via extension
pnpm playwright-cli open --extension

# Use persistent profile (by default profile is in-memory)
pnpm playwright-cli open --persistent
# Use persistent profile with custom directory
pnpm playwright-cli open --profile=/path/to/profile

# Start with config file
pnpm playwright-cli open --config=my-config.json

# Close the browser
pnpm playwright-cli close
# Delete user data for the default session
pnpm playwright-cli delete-data
```

## Snapshots

After each command, playwright-cli provides a snapshot of the current browser state.

```bash
> playwright-cli goto https://example.com
### Page
- Page URL: https://example.com/
- Page Title: Example Domain
### Snapshot
[Snapshot](.playwright-cli/page-2026-02-14T19-22-42-679Z.yml)
```

You can also take a snapshot on demand using `playwright-cli snapshot` command.

If `--filename` is not provided, a new snapshot file is created with a timestamp. Default to automatic file naming, use `--filename=` when artifact is a part of the workflow result.

## Browser Sessions

```bash
# create new browser session named "mysession" with persistent profile
pnpm playwright-cli -s=mysession open example.com --persistent
# same with manually specified profile directory (use when requested explicitly)
pnpm playwright-cli -s=mysession open example.com --profile=/path/to/profile
pnpm playwright-cli -s=mysession click e6
pnpm playwright-cli -s=mysession close  # stop a named browser
pnpm playwright-cli -s=mysession delete-data  # delete user data for persistent session

pnpm playwright-cli list
# Close all browsers
pnpm playwright-cli close-all
# Forcefully kill all browser processes
pnpm playwright-cli kill-all
```

## Local installation

In some cases user might want to install playwright-cli locally. If running globally available `playwright-cli` binary fails, use `npx playwright-cli` to run the commands. For example:

```bash
npx playwright-cli open https://example.com
npx playwright-cli click e1
```

## Example: Form submission

```bash
pnpm playwright-cli open https://example.com/form
pnpm playwright-cli snapshot

pnpm playwright-cli fill e1 "user@example.com"
pnpm playwright-cli fill e2 "password123"
pnpm playwright-cli click e3
pnpm playwright-cli snapshot
pnpm playwright-cli close
```

## Example: Multi-tab workflow

```bash
pnpm playwright-cli open https://example.com
pnpm playwright-cli tab-new https://example.com/other
pnpm playwright-cli tab-list
pnpm playwright-cli tab-select 0
pnpm playwright-cli snapshot
pnpm playwright-cli close
```

## Example: Debugging with DevTools

```bash
pnpm playwright-cli open https://example.com
pnpm playwright-cli click e4
pnpm playwright-cli fill e7 "test"
pnpm playwright-cli console
pnpm playwright-cli network
pnpm playwright-cli close
```

```bash
pnpm playwright-cli open https://example.com
pnpm playwright-cli tracing-start
pnpm playwright-cli click e4
pnpm playwright-cli fill e7 "test"
pnpm playwright-cli tracing-stop
pnpm playwright-cli close
```

## Specific tasks

* **Request mocking** [references/request-mocking.md](references/request-mocking.md)
* **Running Playwright code** [references/running-code.md](references/running-code.md)
* **Browser session management** [references/session-management.md](references/session-management.md)
* **Storage state (cookies, localStorage)** [references/storage-state.md](references/storage-state.md)
* **Test generation** [references/test-generation.md](references/test-generation.md)
* **Tracing** [references/tracing.md](references/tracing.md)
* **Video recording** [references/video-recording.md](references/video-recording.md)
