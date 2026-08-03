# The template ships tooling for building a product, not for maintaining the template

Everything the template contains is inherited by every project made from it.
Tooling whose purpose is maintaining the template's own guidance is therefore
charged to projects that will never use it, and the test applied before anything
is added is a single question: would a project that never edits the template's
guidance still need this file?

Three candidates were declined on that test while this policy was being written.
A validation harness that runs synthetic review scenarios and asserts which
findings an agent must and must not report — valuable, and valuable to whoever
edits the guidance, which is not the project. A decision matrix recording which
parts of an external style guide were adopted, adapted or rejected, pinned to an
upstream commit — that is provenance for the person who made the rulings, while
the project needs only the rulings, which live in the skills. Scheduled review
workflows that open issues about architectural drift — these pass the test, and
were still declined at the template layer, because a review bot inspecting a
three-module prototype either finds nothing or invents something, and one that
cries wolf in week one is muted before month six when it would have paid. Its
prompt is kept as a documented opt-in, since the deduplication protocol in it is
the part that is hard to write.

## Consequences

Guidance that turns out to be wrong is discovered in the first project that
trips over it, and fixed by editing the guidance. That is slower than a harness
and costs nothing to carry.

The rule is a floor, not a ceiling on ambition: tooling a project uses while
building its product belongs here regardless of weight. Skills are the clearest
case — twelve of them ship, because an agent loads one every time it writes a
service or a model. The mirror farm that keeps those skills visible to other
agent harnesses ships for the same reason: a project adds skills of its own, and
the recipe that keeps the mirrors honest is exercised when it does.
