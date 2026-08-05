Previews
========

A **Preview** is a disposable deployment of one branch, created so a change can
be exercised against a real database and a real browser before it merges
(:doc:`ADR-0011 </adr/0011-previews-are-heroku-review-apps>`). It is the
Prototype :doc:`tier <tiers>` with a shorter life: the same manifest, the same
``essential-0`` database, the same single Eco web dyno.

Previews are opt-in *per project*, not per pull request. A project that has not
connected a pipeline has no Previews, and the ``environments.review`` block in
``app.json`` does nothing. A project that connects one gets a Preview for every
pull request automatically.

.. note::

   This template will never have a pipeline of its own. It ships the manifest
   block so that a project which wants Previews inherits it rather than adding
   it — an added block would conflict with every upstream change to
   ``app.json`` thereafter.

Turning Previews on
-------------------

Four steps, once per project.

**1. Have a deployed production app.** The pipeline is created *around* an
existing app, and pointing one at an app that has never been deployed is
undetectable from the pipeline: Previews work perfectly while production serves
Heroku's default welcome page. ``just provision`` is what creates and deploys it
(:doc:`tiers`); ``heroku releases`` should show a ``Deploy`` release, and
``heroku apps:info`` a non-zero slug size, before continuing.

**2. Create the pipeline and connect GitHub.** Previews require both. The
account that connects the repository is the account Previews are billed to, and
it must be verified, since Previews provision add-ons.

.. code-block:: bash

   heroku pipelines:create <project> --app <production-app> --stage production

Connect the GitHub repository from the pipeline's page in the dashboard; the
CLI cannot do it.

While you are there, enable **Automatic deploys** from ``main`` for the
production app. Nothing else makes a merge deploy: review apps deploy branches
and are destroyed on merge, and a single-stage pipeline has no lower stage to
promote from.

.. warning::

   Destroying the only app in a pipeline destroys the pipeline with it, and the
   review-app settings and *Review app config vars* — including
   ``E2E_USER_PASSWORD`` — go too. Reprovision the app without
   ``heroku apps:destroy`` where you can; where you cannot, expect to repeat
   every step on this page.

**3. Enable review apps.**

.. code-block:: bash

   heroku reviewapps:enable --pipeline <project> \
     --autodeploy --autodestroy --wait-for-ci

``--wait-for-ci`` is safe here only because the CI workflow runs on every
commit. If a project reintroduces ``paths-ignore`` to ``.github/workflows/ci.yml``,
a documentation-only pull request will report no status and its Preview will
wait forever.

Then set the stale-app timer to **1 day** in the pipeline's Review Apps
settings. Previews are throwaway; one that has not been visited in a day has
served its purpose, and re-creating it is a button on the pull request.

**4. Set the seed password.** In the pipeline's *Review app config vars*, set
``E2E_USER_PASSWORD``. These variables are injected into every Preview and are
the only sensible place for a credential — ``app.json`` is in the repository.

Logging in
----------

Every Preview is seeded by ``manage.py create_e2e_user``, run from
``postdeploy``, which creates ``e2e@test.local`` with a **verified** email
address and the password from ``E2E_USER_PASSWORD``. The verification matters:
production settings make ``ACCOUNT_EMAIL_VERIFICATION`` mandatory and a Preview
has no Mailgun key, so an unverified account cannot log in and its confirmation
link goes to the dyno log.

That is the same account the Playwright suite uses, so the e2e specs can be
pointed at a Preview as well as at a local server.

.. warning::

   ``create_e2e_user`` refuses to run with ``DEBUG`` off unless a password is
   supplied. A Preview is on the public internet, and the command's built-in
   default password is published in this repository.

Signup itself does not work on a Preview for the same reason — mandatory
verification, no mail provider. Confirmation links are readable with
``heroku logs --app <preview-app>`` if you need a second account.

What a Preview costs
--------------------

Heroku prorates dynos and add-ons **to the second**, so the interesting number
is hours awake, not months.

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Component
     - Rate
     - A Preview visited an hour a day
   * - Eco web dyno
     - Pooled hours, asleep after 30 min idle
     - ~45 h/month of the pool
   * - Postgres ``essential-0``
     - ~$0.007/hr
     - ~$0.17/day until destroyed

A Preview nobody opens costs roughly the half-hour its dyno takes to fall
asleep, plus its database until the timer fires.

.. warning::

   **Preview hours come out of the account-wide Eco pool.**

   The pool is 1000 hours a month, shared by every Eco dyno on the account, and
   :doc:`tiers` explains what happens when it runs out: every Eco dyno sleeps
   for the rest of the month and the hours cannot be topped up. Heroku emails a
   warning at 80%.

   Ten Previews visited an hour a day is roughly 450 hours — comfortable. Ten
   Previews being polled continuously by an agent never sleep, and that is
   7300 hours. If Previews are exercised continuously rather than opened and
   read, move them to Basic dynos by setting ``size`` in
   ``environments.review.formation``.

   Eco is unavailable on a Heroku Team at all, so a Team project must set that
   ``size`` regardless.

What a Preview does not do
--------------------------

Everything :doc:`the Prototype tier does not do <tiers>` applies, and one more
thing does. The Eco and Basic plans forbid mixing dyno types and allow one dyno
per process type, so a Preview is **web-only**: no worker, no Celery beat, no
key-value store. Tasks run inline inside the request, and Heroku's thirty-second
request timeout applies to them.

Errors go to the dyno log and nowhere else, because ``SENTRY_DSN`` is unset. If
you set one as a review app config var, set ``SENTRY_ENVIRONMENT`` alongside it
or Preview errors will arrive in Sentry as production issues.
