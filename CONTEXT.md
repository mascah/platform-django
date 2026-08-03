# platform-django

A project template for spinning out new web applications. Its two defining
concerns are running the same codebase across very different places — a laptop
with several worktrees, an agent's cloud VM, CI, Heroku — and letting a copy of
the template stay close enough to its origin that improvements can flow in both
directions.

## Language

### Running the code

**Environment**:
A place the code runs. The developer's machine, a worktree, an agent's cloud VM,
and CI are all environments. It never means a deployment stage — that is a Tier.
_Avoid_: env (as a noun for deployment stage), stage, instance

**Worktree**:
An isolated checkout of a branch that can run the whole application alongside
other worktrees on the same machine.
_Avoid_: workspace, sandbox, branch

**Worktree ID**:
The identifier that distinguishes one worktree's runtime resources from
another's. Stable for the life of the worktree.

**Backing service**:
A stateful dependency the application connects to rather than runs in-process:
Postgres and Redis. Shared across all worktrees on a machine; worktrees are
separated inside them logically, not by running more of them.
_Avoid_: infrastructure, container, dependency

**Application process**:
The parts of the system a developer runs directly rather than as a backing
service: Django and Vite.

**Bootstrap**:
Making a fresh checkout runnable. Must succeed unattended in any environment,
including as root on a machine that has never seen this project.
_Avoid_: install, provision, setup

**Setup**:
One-time configuration of a developer's own machine — shell integration,
personal tooling, git hooks. Convenience only; the application never depends on
it having been run.

**Remote environment**:
An environment the developer cannot reach into: an ephemeral VM with a fresh
clone, no access to their machine, and no state carried over between runs.

### Shipping the code

**Tier**:
The deployment shape a project is running at, defined by which paid capabilities
are provisioned for it. Moving between tiers changes what is provisioned, never
what the code says.
_Avoid_: environment, stage, plan

**Tier 0 / Prototype**:
The cheapest shape a project can be deployed in, running without any capability
that costs more than the minimum.

**Tier 1 / Traction**:
The shape a project takes once real background work or a shared cache is worth
paying for.

**Tier 2 / Production**:
The shape a project takes once it must be continuously available.

### Copying the template

**Project slug**:
The identifier distinguishing one copy of the template from another at runtime.
It is the only thing about a copy's identity that the code reads.
_Avoid_: project name, app name, module name

**Display name**:
The product name a person sees. Unrelated to the project slug, and never used to
name a resource.

**Upstream template**:
This repository, viewed from a project created out of it.

**Downstream project**:
A project created out of the template, viewed from the template. Its code stays
byte-identical to the upstream template so that changes can be merged in either
direction.
_Avoid_: fork, child, instance

**Template-owned module**:
A module the template ships and continues to evolve. A downstream project
inherits from it and extends it, and expects to receive changes to it.

**Project-owned module**:
A module a downstream project adds, which the template knows nothing about. It
is where anything specific to one project belongs.
