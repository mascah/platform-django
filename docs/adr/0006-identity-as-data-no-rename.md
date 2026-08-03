# Projects created from this template are not renamed; identity is data

A project created from this template keeps the template's package, directory and
module names verbatim. What distinguishes one project from another is data — a
project slug, a display name, a repository name, a deployed application name,
and per-project credentials — never a change to the source.

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

The accepted cost is cosmetic: a project's internal package name is the
template's, which reads oddly in imports and appears in static asset paths. It
is invisible to users of the application and cannot collide, since projects
never share an interpreter. Where a name is genuinely user-facing, the display
name is used; where a name identifies a resource, the project slug is.
