# mise manages the toolchain; bootstrap and setup are separate layers

Bootstrap is OS-agnostic, idempotent, and assumes nothing about the machine
beyond a shell — it must succeed as root on a fresh Ubuntu VM that has never
seen this project. Setup keeps the parts that only make sense on a developer's
own macOS machine. mise installs the pinned toolchain in both, replacing
Homebrew, pyenv, nvm and direnv.

## Considered Options

The previous script hard-failed without Homebrew, appended to the user's shell
profile, and built Python through pyenv — none of which is available or
affordable in a remote environment that must finish provisioning in a few
minutes. pyenv had already been made redundant by uv, so the only real gap was
installing a pinned Node and the task runner on a non-macOS machine without a
package manager, which is the narrow job mise is being adopted for.

direnv is removed rather than kept alongside: mise's maintainers state that the
two should not be used together and decline compatibility fixes, and with URL
composition moved into settings (ADR-0001) nothing needs a shell hook to compute
anything — only to load a file.

## Consequences

The idiomatic version files stay authoritative and mise reads them rather than
replacing them, because the deployment platform reads the same files to choose
the Python and Node versions it builds with. Deleting them in favour of a single
mise config would silently change the deployed runtime.
