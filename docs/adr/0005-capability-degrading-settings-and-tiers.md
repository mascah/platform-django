# Settings degrade to match provisioned capabilities, defining the deployment tiers

Settings branch on whether a capability has been provisioned rather than on
which tier a project is meant to be at. With no Redis available the cache is
in-process and background tasks run inline; when Redis appears, the real cache
and a real queue take over. One deployable artifact, one production settings
module, several runtime shapes.

## Considered Options

Separate settings modules per tier were rejected because the tiers would drift
apart and eventually a project would be deployed with the wrong one. A single
always-on configuration was rejected on cost: it makes every prototype pay for a
key-value store it does not use, and — because the cheapest dyno plan's hours
are pooled across the whole account and a worker process never sleeps — a single
prototype running a worker can exhaust the pool and force every other prototype
in the account to sleep for the rest of the month.

## Consequences

Application code is written the same way at every tier: tasks are declared and
dispatched normally, the cache is used normally. Graduating a project is
provisioning an add-on and scaling a process — no code change, no settings
rewrite, no migration.

The prototype tier's limits follow from this and must be stated wherever it is
documented: an in-process cache is only a cache while there is one process,
inline tasks make slow work into slow responses, and periodic jobs need the
platform's scheduler rather than a long-running beat process. In particular,
sessions must stay in the database — moving them into the cache to save a query
would log every user out whenever a dyno restarts.
