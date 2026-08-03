# Projects created from this template are not renamed; identity is data

A project created from this template does not rename what the template arrived
with: the package, directories and modules the template ships keep their names.
What distinguishes one project from another is data — a project slug, a display
name, a repository name, a deployed application name, and per-project
credentials — never a mass renaming of the source.

This constrains only the names the template brought. Everything a project adds
is named freely: new domain modules, new frontend applications, new packages.
Those are additions, and additions merge cleanly.

## Considered Options

Renaming was the previous approach and touched 74 files. The cost is not running
the rename; it is that every renamed file is a file that can no longer be merged
between the template and the projects made from it, and those are exactly the
files an improvement would arrive in. Because improvements are expected to flow
in both directions — the template absorbs what a real project learned, projects
receive what the template gained — the rename converts every future exchange
into a manual port. Templating engines were rejected for the weight they add to
a repository meant to be cloned and thrown away cheaply.

## Consequences

Each project keeps a remote pointing at the template, so receiving an
improvement is a merge and contributing one back is a cherry-pick, with no
conflicts arising from naming.

The remaining merge surface is the small set of files where a project registers
what it has added — the installed-application list, the root URL configuration,
the workspace manifest, the import contracts. These are append-mostly lists, so
conflicts there are the cheap kind, but they are the files to keep tidy: a
project that reorders or restructures them is choosing to make every future
merge harder, and gains nothing for it.

The accepted cost is cosmetic: a project's internal package name is the
template's, which reads oddly in imports and appears in static asset paths. It
is invisible to users of the application and cannot collide, since projects
never share an interpreter. Where a name is genuinely user-facing, the display
name is used; where a name identifies a resource, the project slug is.
