Working With the Template
=========================

A project created from this template keeps a remote pointing back at it.
Receiving an improvement is a merge, contributing one back is a cherry-pick, and
neither involves a rename because nothing was renamed to begin with
(:doc:`ADR-0006 </adr/0006-identity-as-data-no-rename>`).

This guide is about making a project, what staying connected costs in practice,
and where to put a change so it costs as little as possible.

Creating a project
------------------

A new project is a clone plus two values::

    git clone https://github.com/mascah/platform-django.git acme-app
    cd acme-app
    bin/bootstrap

``bin/bootstrap`` writes ``.env``, and ``PROJECT_SLUG`` arrives already set to
the checkout's directory name --- so two projects on one machine have separate
databases, cache keys and task queues without either being renamed. Set the
display name beside it, quoted, since it is the one value here that usually
contains a space::

    PROJECT_SLUG=acme_app              # names resources: databases, queues, the deployed app
    PROJECT_DISPLAY_NAME="Acme App"    # what a user reads: titles, landing page, emails

The internal Python package stays ``platform_django`` in every project. That is
the point, and it is invisible to users of the application.

Then point the clone at its own repository, keeping the template as a second
remote::

    git remote rename origin template
    gh repo create <owner>/acme-app --private --source=. --remote=origin --push

Four more things carry the template's identity rather than the project's, and
none of them is a rename --- they are values a human reads:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - File
     - Change
   * - ``README.md``
     - The title, the tagline, and the "Making a Project From This Template"
       section. Everything below that section is true of a project as written.
   * - ``app.json``
     - The manifest ``name``, and the ``PROJECT_SLUG`` /
       ``PROJECT_DISPLAY_NAME`` values --- otherwise the project deploys under
       the template's name.
   * - ``CLAUDE.md``
     - The line naming the issue repository, so agents file against the project.
   * - ``docs/agents/issue-tracker.md``
     - The same repository reference.

Adding domain modules and frontend applications is unaffected: those are
additions, named freely, and additions merge cleanly.

The merge surface
-----------------

The thing to understand first is what actually conflicts.

The merge surface is **not** the set of files that differ between a project and
the template. It is the set of files where both sides changed the *same lines*.
Divergence on its own is free. A project can add fifty modules, rewrite the
landing page and never touch a template file, and every future merge stays
clean.

This is why ADR-0006 describes the cost as "proportional to what actually
diverged, rather than charged up front against every file."

It also means contributing back is opt-in per commit. You never push a project's
branch upstream; you cherry-pick the commits worth donating. A change staying in
the project is the default, not a special case that needs arranging.

Three tiers of divergence
-------------------------

Reach for the cheapest tier that does the job.

**Change an environment variable.** No merge surface at all. The value lives in
a deployment, not in a tracked file, so the template can rewrite the line that
reads it and nothing collides. Most production differences belong here — see
:doc:`configuration`.

**Add a new file.** No merge surface either, and there never will be. Git merges
two additions of different files without consulting either. This is where
anything project-specific belongs: new modules, new frontend apps, new CI
workflows, new ADRs.

**Edit a template-owned file.** One ordinary conflict, and only when the
template happens to touch the same hunk. This is allowed and sometimes correct.
It is simply the only tier that costs anything.

ADR-0006 notes that project-specific code accumulating in a template-owned file
is usually a signal rather than a problem: either the change is generally useful
and should go upstream, or it is specific and wants a file of its own.

Receiving and contributing
--------------------------

.. code-block:: bash

    # Once, in the project
    git remote add template https://github.com/mascah/platform-django.git

    # Receive an improvement from the template
    git fetch template
    git merge template/main

    # Contribute one back
    git checkout -b improvement template/main
    git cherry-pick <commit>
    git push template improvement   # then open a pull request

The files that routinely conflict are the append-mostly lists where a project
registers what it has added --- ``INSTALLED_APPS``, the root URL configuration,
``pnpm-workspace.yaml``, ``.importlinter``. Keep them in template order. A
project that reorders or restructures them makes every future merge harder and
gains nothing for it.

The generated API client
------------------------

``apps/platform_django/src/services/platform_django/`` is committed to the tree
and generated wholesale from Django's OpenAPI schema. A project with its own
models rewrites it; so does the template whenever a serializer changes.

**Never resolve these files as a merge. Regenerate them.**

.. code-block:: bash

    just openapi

The merged Python is the source of truth, and the only correct content for these
files is whatever the generator produces from it. A textual merge of two
generated files is meaningless by construction.

The trap is that git usually will not warn you. drf-spectacular sorts schema
components alphabetically, so a project's added types interleave with the
template's rather than overlapping them, and git merges the hunks cleanly. The
result compiles, matches no schema that has ever existed, and looks in review
exactly like a correct merge. **A clean auto-merge of the generated client is
not evidence that it is right.**

CI runs an ``openapi-client`` job that regenerates the client and fails on any
diff, so this is checked rather than merely remembered. After any merge touching
serializers, views, schema annotations or the generator config: run
``just openapi`` and commit whatever it produces.

CI workflows
------------

Put project-specific CI in its own workflow file --- ``deploy.yml``,
``ci-project.yml``, whatever it is. GitHub runs every file in
``.github/workflows/``, so a new one needs no registration anywhere and will
never conflict.

Editing ``ci.yml`` itself is the third tier. The ``paths-filter`` blocks are
append-mostly lists, so adding a project's paths to them is the cheap kind of
change. Structural edits --- dropping a job, changing a service image --- cost
one ordinary conflict whenever the template touches the same region. Keep such
edits at the edges of the file rather than woven through the middle.

Migrations
----------

Migrations travel one way. The template's arrive with a merge; a project's are
never cherry-picked back, because they describe that project's schema.

That still leaves the same trap as the generated client. A project adding a
migration to ``platform_django.users`` while the template adds one too produces
two ``0002_`` files --- different filenames, both additions, merged cleanly ---
and a migration graph with two leaves that Django will not apply.

``django-linear-migrations`` makes that collide instead. Each app carries a
``migrations/max_migration.txt`` naming its latest migration, so two branches
adding a migration to the same app change the same line and the merge stops.
Resolve it by rebasing the migration rather than by editing the file::

    python manage.py rebase_migration <app_label>

A system check fails if the file falls out of step with the directory, so it
cannot quietly rot.

The same applies within one project: two worktrees, or two agents, each adding a
migration to the same app now conflict at merge rather than at ``migrate``.

Backward compatibility
^^^^^^^^^^^^^^^^^^^^^^

``django-migration-linter`` runs in CI over the migrations a branch adds, and
fails on operations that break a process still running the old code --- dropping
or renaming a column or table, adding a ``NOT NULL`` column without a default,
altering a column's type. Migrations are applied before new code is serving, so
that window is real on any deployment that does not stop the world.

The usual fix is to split the change across two deploys: add the new column,
ship code that writes both, backfill, then drop the old one. Where a migration
is genuinely safe for a reason the linter cannot see, mark it::

    from django_migration_linter import IgnoreMigration


    class Migration(IgnoreMigration, migrations.Migration):
        ...

Architecture decision records
-----------------------------

**Downstream projects number their ADRs from 1001.** The template keeps the low
numbers; a project writing its first ADR creates
``docs/adr/1001-<slug>.md``.

Without the band, a project's first ADR is ``0011-`` and so is the template's
next one. Those are two different filenames and both are additions, so git
merges them cleanly --- leaving the repository holding two ADR-0011s and every
cross-reference to "ADR-0011" ambiguous. As with the generated client, the
failure is the absence of a conflict rather than the presence of one.

Keep the ADRs the template shipped. They still describe machinery the project is
still running, and deleting a file the template continues to maintain turns
every future edit to it into a delete/modify conflict. Where a project's
decision contradicts an inherited one, write a project ADR that says so and
supersedes it.

New ADRs need no registration: they are not listed in the ``index.rst``
toctree, and ``docs/conf.py`` suppresses the warning that would otherwise cause.
Adding one touches no shared file.

Production settings
-------------------

Reach for the tiers in order.

Most production differences are configuration, and
``config/settings/production.py`` already reads the environment for them ---
allowed hosts, the admin URL, HSTS, database connection age, email, Sentry, the
API server URL. Set the variable in the deployment and change nothing tracked.

For project-specific settings *code*, ``production.py`` ends with a
``# Your stuff...`` marker. The template's own edits happen above it, so
appending below is the lowest-conflict place in the file.

Only if that block grows large is a separate settings module worth it: a
project-owned file that imports from ``config.settings.production`` and
overrides, with ``DJANGO_SETTINGS_MODULE`` pointed at it. That is tier two, at
the cost of one more indirection --- do not reach for it before the appended
block earns it.

When to stop
------------

A project that has its own infrastructure, its own deployment story and nothing
left it wants to receive runs ``bin/eject``
(:doc:`ADR-0007 </adr/0007-ejecting-from-the-template>`)::

    bin/eject acme_app                      # display name derived: "Acme App"
    bin/eject acme_app "ACME Rocket Sled"   # or given explicitly

It renames the package, the workspace application and every reference to them,
drops the ``template`` remote, regenerates the lockfiles, and deletes itself.
Links that point at the template's *own* repository are left alone and listed,
because renaming a clone URL only produces one that resolves to nothing.

``PROJECT_SLUG`` and ``PROJECT_DISPLAY_NAME`` stay --- they are ordinary
configuration, not template scaffolding. Only their defaults move.

This is the line worth holding before then. Renaming a *value* a human reads is
free; renaming an *identifier* Python, pnpm or import-linter resolves is
ejecting by hand, and costs the ability to merge without buying the exit.

It is one-way. It refuses to run against a dirty tree so that ``git reset
--hard`` is a real undo in the minute afterwards, but there is no route back
once you have built on it. Do it when you have decided you will never merge with
the template again; until then the rename buys nothing and costs the ability to.
