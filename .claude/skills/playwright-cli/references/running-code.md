# Running Custom Playwright Code

Use `run-code` to execute arbitrary Playwright code for advanced scenarios not covered by CLI commands.

## Syntax

```bash
pnpm playwright-cli run-code "async page => {
  // Your Playwright code here
  // Access page.context() for browser context operations
}"
```

## Geolocation

```bash
# Grant geolocation permission and set location
pnpm playwright-cli run-code "async page => {
  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 37.7749, longitude: -122.4194 });
}"

# Set location to London
pnpm playwright-cli run-code "async page => {
  await page.context().grantPermissions(['geolocation']);
  await page.context().setGeolocation({ latitude: 51.5074, longitude: -0.1278 });
}"

# Clear geolocation override
pnpm playwright-cli run-code "async page => {
  await page.context().clearPermissions();
}"
```

## Permissions

```bash
# Grant multiple permissions
pnpm playwright-cli run-code "async page => {
  await page.context().grantPermissions([
    'geolocation',
    'notifications',
    'camera',
    'microphone'
  ]);
}"

# Grant permissions for specific origin
pnpm playwright-cli run-code "async page => {
  await page.context().grantPermissions(['clipboard-read'], {
    origin: 'https://example.com'
  });
}"
```

## Media Emulation

```bash
# Emulate dark color scheme
pnpm playwright-cli run-code "async page => {
  await page.emulateMedia({ colorScheme: 'dark' });
}"

# Emulate light color scheme
pnpm playwright-cli run-code "async page => {
  await page.emulateMedia({ colorScheme: 'light' });
}"

# Emulate reduced motion
pnpm playwright-cli run-code "async page => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
}"

# Emulate print media
pnpm playwright-cli run-code "async page => {
  await page.emulateMedia({ media: 'print' });
}"
```

## Wait Strategies

```bash
# Wait for network idle
pnpm playwright-cli run-code "async page => {
  await page.waitForLoadState('networkidle');
}"

# Wait for specific element
pnpm playwright-cli run-code "async page => {
  await page.waitForSelector('.loading', { state: 'hidden' });
}"

# Wait for function to return true
pnpm playwright-cli run-code "async page => {
  await page.waitForFunction(() => window.appReady === true);
}"

# Wait with timeout
pnpm playwright-cli run-code "async page => {
  await page.waitForSelector('.result', { timeout: 10000 });
}"
```

## Frames and Iframes

```bash
# Work with iframe
pnpm playwright-cli run-code "async page => {
  const frame = page.locator('iframe#my-iframe').contentFrame();
  await frame.locator('button').click();
}"

# Get all frames
pnpm playwright-cli run-code "async page => {
  const frames = page.frames();
  return frames.map(f => f.url());
}"
```

## File Downloads

```bash
# Handle file download
pnpm playwright-cli run-code "async page => {
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.click('a.download-link')
  ]);
  await download.saveAs('./downloaded-file.pdf');
  return download.suggestedFilename();
}"
```

## Clipboard

```bash
# Read clipboard (requires permission)
pnpm playwright-cli run-code "async page => {
  await page.context().grantPermissions(['clipboard-read']);
  return await page.evaluate(() => navigator.clipboard.readText());
}"

# Write to clipboard
pnpm playwright-cli run-code "async page => {
  await page.evaluate(text => navigator.clipboard.writeText(text), 'Hello clipboard!');
}"
```

## Page Information

```bash
# Get page title
pnpm playwright-cli run-code "async page => {
  return await page.title();
}"

# Get current URL
pnpm playwright-cli run-code "async page => {
  return page.url();
}"

# Get page content
pnpm playwright-cli run-code "async page => {
  return await page.content();
}"

# Get viewport size
pnpm playwright-cli run-code "async page => {
  return page.viewportSize();
}"
```

## JavaScript Execution

```bash
# Execute JavaScript and return result
pnpm playwright-cli run-code "async page => {
  return await page.evaluate(() => {
    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      cookiesEnabled: navigator.cookieEnabled
    };
  });
}"

# Pass arguments to evaluate
pnpm playwright-cli run-code "async page => {
  const multiplier = 5;
  return await page.evaluate(m => document.querySelectorAll('li').length * m, multiplier);
}"
```

## Error Handling

```bash
# Try-catch in run-code
pnpm playwright-cli run-code "async page => {
  try {
    await page.click('.maybe-missing', { timeout: 1000 });
    return 'clicked';
  } catch (e) {
    return 'element not found';
  }
}"
```

## Complex Workflows

```bash
# Login and save state
pnpm playwright-cli run-code "async page => {
  await page.goto('https://example.com/login');
  await page.fill('input[name=email]', 'user@example.com');
  await page.fill('input[name=password]', 'secret');
  await page.click('button[type=submit]');
  await page.waitForURL('**/dashboard');
  await page.context().storageState({ path: 'auth.json' });
  return 'Login successful';
}"

# Scrape data from multiple pages
pnpm playwright-cli run-code "async page => {
  const results = [];
  for (let i = 1; i <= 3; i++) {
    await page.goto(\`https://example.com/page/\${i}\`);
    const items = await page.locator('.item').allTextContents();
    results.push(...items);
  }
  return results;
}"
```
