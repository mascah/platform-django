# A Preview is a Heroku review app on the same manifest, seeded and thrown away

A Preview is one branch deployed from the manifest every other deployment uses,
provisioned by a Heroku pipeline when a pull request opens and destroyed when it
closes or after a day of nobody looking at it. `app.json` gains an
`environments.review` block whose only content is a `postdeploy` script; the
database plan, the dyno size and every config variable are inherited from the
manifest's top level, so a Preview is the Prototype tier with a shorter life.

The template will never have a pipeline of its own. The block ships anyway,
inert, because a downstream project that added it itself would own a permanent
conflict in `app.json` against every upstream change to that file (ADR-0006).

## Considered Options

**Heroku CI was rejected.** It is a separate product, billed from `standard-1x`
upwards and defaulting to Performance-M, and it cannot use the Eco plan at all.
It would duplicate a subset of a GitHub Actions suite that already runs a
bootstrap-in-a-clean-container job, two drift checks and a browser suite, none
of which it can do. GitHub Actions remains the only CI; the pipeline exists
solely because review apps require one.

**SQLite was rejected**, and the reason is not cost. `Procfile` declares
`release: python manage.py migrate`, and a release dyno has its own ephemeral
filesystem that is discarded when it exits. Migrations would be applied to a
file no web dyno ever sees, so the app would boot against no database rather
than a stale one. Keeping it working would mean migrating from the web process
instead — a fork in the Procfile serving a deployment stage, which is precisely
what ADR-0005 refused — plus a SQLite branch in `config/env.py`, plus
`database is locked` under `ATOMIC_REQUESTS` and multiple gunicorn workers. The
saving would have been under a dollar per Preview: Heroku prorates add-ons to
the second, so `essential-0` costs roughly seven tenths of a cent per hour.

**Eco was chosen over Basic dynos** knowing the risk. Preview dynos draw on the
same account-wide 1000-hour pool as every other Eco dyno, and exhausting it puts
every Eco dyno on the account to sleep for the remainder of the month, with no
way to buy more. What makes it tolerable is that a Preview is web-only and Eco
web dynos sleep after thirty minutes idle and consume nothing while asleep, so
a Preview visited for an hour a day costs about 45 hours a month; Heroku warns
by email at 80% of the pool. ADR-0005's warning is about *worker* dynos, which
never sleep because they answer no web requests — it does not apply here. Basic
dynos remain the answer for a project whose Previews are exercised continuously,
and are the only answer on a Heroku Team, where Eco is unavailable.

## Consequences

**A Preview must be seeded, or it cannot be logged into.** Production settings
make `ACCOUNT_EMAIL_VERIFICATION` mandatory and no Preview has a Mailgun key, so
signup dead-ends with a confirmation link in the dyno log. `create_e2e_user`
therefore creates a verified `EmailAddress` alongside the user, and runs from
`postdeploy` rather than the manifest's top level so that `heroku create
--manifest` never seeds a test account into a real app. Its password comes from
a review app config variable on the pipeline, and it refuses its built-in
default whenever `DEBUG` is off, because a Preview is on the public internet.

**CI runs on every commit, with no `paths-ignore`.** A Preview created with
"wait for CI to pass" waits on a status that a skipped workflow never reports,
so a docs-only pull request would hang indefinitely. The filter cost nothing to
remove: the `changes` job already skips the expensive jobs on a docs-only
change. Re-adding `paths-ignore` for speed would break Previews in a way visible
nowhere in the repository.

**A Preview has no worker and no key-value store.** The Eco and Basic plans
forbid mixing dyno types and allow one dyno per process type, so tasks run
inline and the thirty-second request timeout applies to them, exactly as at the
Prototype tier.

**A Preview reports errors nowhere but its own log**, since `SENTRY_DSN` is
unset by default. Setting one as a review app config variable requires setting
`SENTRY_ENVIRONMENT` with it, or Preview errors arrive as production issues.
