# Ejecting is the one-way exit from the template, and it renames

A project that has outgrown the template — its own infrastructure, its own
deployment story, nothing left it wants to receive — runs `bin/eject`. That
renames what the template brought, drops the template remote, and deletes the
script. Afterwards the project is an ordinary repository that happens to have
started here.

This does not contradict ADR-0006, it bounds it. That decision's whole argument
is about preserving mergeability: "every renamed file is a file that can no
longer be merged." The argument is conditional on wanting to merge. Once a
project has decided it never will again, the rename costs nothing it still
values, and the odd-reading package name stops being an accepted cost and
becomes pointless.

So the two decisions divide the lifecycle rather than competing: identity is
data while a project is connected, and a rename is what disconnecting means.

## Considered Options

Renaming at clone time was the previous approach, and it is the one this
replaces. The mistake was never the rename itself — it was doing it on day one,
charging all 74 files against every project before anyone knew whether that
project would ever diverge. Most never do. Moving the same operation to the end
of the lifecycle charges it once, to the projects that earned it.

Leaving no exit at all was considered and rejected as wishful: a project running
its own Terraform, cluster and release process is not going to keep a package
named after a template it stopped tracking, and without a supported exit it
would get an unsupported one — a hand-rolled find-and-replace at exactly the
moment the project has become important enough that a subtle miss is expensive.

Producing a fresh repository with no template history was rejected for the case
this serves. A project mature enough to eject has a history worth keeping, and
most of it is its own.

## Consequences

Ejecting is not reversible in practice. `git reset --hard` undoes it in the
minute after, which is why the script refuses to run against a dirty tree, but
once the rename is committed and built on, coming back means merging against a
history that no longer shares any of the renamed files.

The environment contract survives. `PROJECT_SLUG` and `PROJECT_DISPLAY_NAME` are
ordinary configuration, not template scaffolding, and a project running several
environments wants them more rather than less; only their defaults move to the
new name. What ejecting removes is the template remote and the template's name,
not the practice of keeping identity in the environment.

Names that point at the template's own repository are deliberately left behind —
a clone URL, an `owner/repo` reference, a documentation link. Renaming those
would produce URLs that look right and resolve to nothing. The script reports
each one it kept, because they sit in prose that an ejected project should be
rewriting anyway rather than repointing.

Static asset paths move with the package, so a project that ejects after it is
already deployed changes the URLs its collected static files are served from.
That is a deploy-ordering concern, and the only consequence of the rename that
is not cosmetic.
