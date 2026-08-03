Deployment Tiers
================

Settings branch on whether a capability has been *provisioned*, never on which
tier a project is meant to be at (:doc:`ADR-0005 </adr/0005-capability-degrading-settings-and-tiers>`).
There is one deployable artifact and one production settings module; the tiers
below are the runtime shapes it takes.

A tier is therefore a diff to ``app.json`` plus a scale command. Choose one
deliberately from what follows rather than discovering it after a surprise.

.. note::

   Prices are Heroku's published monthly rates and are quoted so the tiers can
   be compared, not as a guarantee. Check
   `Heroku pricing <https://www.heroku.com/pricing/>`_ before committing.

The tiers
---------

.. list-table::
   :header-rows: 1
   :widths: 14 12 34 40

   * - Tier
     - Cost
     - Components
     - What it adds over the tier below
   * - Prototype
     - **$10/mo**
     - 1 Eco web dyno ($5), Postgres Essential-0 ($5)
     - The floor. What ``app.json`` provisions as it stands.
   * - Always-on
     - **$12/mo**
     - 1 Basic web dyno ($7), Postgres Essential-0 ($5)
     - The web dyno stops sleeping, so the first request after a quiet
       period is not slow, and the account-wide hours pool stops applying.
   * - Background work
     - **$22/mo**
     - Adds Key-Value Store Mini ($3) and 1 Basic worker dyno ($7)
     - A shared cache and a real queue. Tasks stop running inline, so a slow
       job stops being a slow response.
   * - Production
     - **$65/mo+**
     - Standard-1X web ($25) and worker ($25), Postgres Essential-2 ($20)
       or Standard-0 ($50), Key-Value Store Premium-0 ($15)
     - Horizontal scaling, metrics, zero-downtime deploys, a database with
       a real connection limit and rollback.

Graduating
----------

Provision an add-on and scale a process. There is no code change, no settings
rewrite, and no migration --- application code is written the same way at every
tier, because it is the presence of the capability that settings react to.

.. code-block:: bash

   # Prototype → Always-on
   heroku ps:type web=basic

   # Always-on → Background work
   heroku addons:create heroku-redis:mini
   heroku ps:scale worker=1

Record the change in ``app.json`` at the same time, so a second app provisioned
from the manifest arrives at the tier you are actually running.

What the prototype tier does not do
-----------------------------------

With no key-value store attached, the cache is ``LocMemCache`` and task dispatch
is eager. Both are real, working implementations --- and both have limits that
are easy to mistake for bugs later:

**An in-process cache is only a cache while there is one process.** Each dyno
holds its own copy, nothing is shared, and everything is lost on restart or
deploy. Never cache anything two requests must agree on --- a rate-limit
counter, a lock, an idempotency key. Those need the shared store.

**Inline task execution turns slow work into slow responses.** ``.delay()``
still works, but it runs the task in the request/response cycle instead of
queueing it. A task that takes ten seconds is a ten-second response, and a
30-second Heroku request timeout is a failed one. Keep tasks short until there
is a worker.

**Periodic jobs need the platform scheduler.** Celery beat is a long-running
process, which means a second dyno drawing hours continuously --- exactly what
this tier is avoiding. Use `Heroku Scheduler
<https://devcenter.heroku.com/articles/scheduler>`_ to run a management command
on a schedule instead.

.. warning::

   **A worker on the Eco plan never sleeps, and the hours are pooled across
   your whole account.**

   The Eco plan is 1000 dyno hours per month for $5, and that pool is shared by
   every Eco dyno on the account. Web dynos sleep after 30 minutes of
   inactivity, so several idle prototypes cost very little. Worker dynos do
   not sleep --- they answer no web requests, so there is no idle to detect.

   A single Eco worker running continuously consumes roughly 730 hours a month,
   nearly three quarters of the pool. When the pool is exhausted, **every Eco
   dyno on the account is forced to sleep for the rest of the month** and the
   hours cannot be topped up. One prototype running a worker can therefore take
   every other prototype in the account down with it.

   If a project needs a worker, put it on Basic dynos ($7 each) rather than
   scaling a worker on Eco.

.. warning::

   **Do not move sessions into the cache.**

   Sessions stay in the database at every tier. The database-backed session
   store costs a query per request, and moving to the cache to save it is a
   standing temptation --- but at the prototype tier the cache is in-process, so
   every dyno restart, deploy, or scale-out would log every user out. Even with
   a shared store, the cache is eviction-backed by design and sessions are not
   evictable data.

   ``SESSION_ENGINE`` is pinned to the database backend in
   ``config/settings/base.py`` and is not tier-dependent. Leave it there.
