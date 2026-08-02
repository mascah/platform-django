# Configuration file for the Sphinx documentation builder.
#
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------

project = "Platform Django"
copyright = "2026, Mike Ascah"  # noqa: A001
author = "Mike Ascah"
version = "1.0"
release = "1.0.0"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "myst_parser",  # Markdown support
]

# Support both reStructuredText and Markdown
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# MyST-Parser configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]

# List of patterns to ignore when looking for source files.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "plans"]

# Docs aimed at agents/tooling live outside the reader-facing toctree; don't let
# the -W build fail over them. Real reference errors still break the build.
suppress_warnings = ["toc.not_included"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": True,
}

# Show TODO items
todo_include_todos = True
