---
name: django-model
description: Use when adding, changing, or reviewing Django model fields, constraints, validation, properties, methods, relations, or save behavior under platform_django/.
---

# Django Model

Start by reading the target model and the nearest model, service, selector, and
test files. Follow current module code before older prose.

## Decide

- Put durable integrity in database constraints and indexes: `UniqueConstraint`,
  `CheckConstraint`, `unique=True`, and `db_index=True` where appropriate. A
  rule the database enforces holds against every write path, including
  migrations, fixtures and the admin.
- Use `clean()` only for simple validation over the model's own local fields,
  and only when that improves the write contract or the error reporting.
- Keep relational or complex business validation in services.
- Keep relational, query-producing, or cross-row computed values in selectors.
  Model properties and methods stay local-field only.
- Do not put business behavior in `save()`.
- Do not require universal `full_clean()` before save. Call it only where model
  validation is intentionally part of that specific write path.

## Relations across modules

A foreign key to another module's model needs a stated justification of a
particular kind:

- ownership or referential integrity best enforced in the database;
- lifecycle coupling tight enough that an integer identifier would lose a
  guarantee the project needs;
- reverse traversal that is actually used.

The list is illustrative, not closed — what is required is a stated reason of
that kind, written where the field is declared. `ForeignKey(settings.AUTH_USER_MODEL)`
recording who owns a row is the ordinary case.

Absent such a reason, refer to the other module's rows by integer identifier.
Where a relation is justified but nothing traverses it backwards, declare it
`related_name="+"` — that is what keeps a one-way dependency from becoming a
two-way one through the reverse accessor.

Within a single module, foreign keys need no justification.

## Tests

- Add targeted tests near the owning module's existing model, service, or
  selector tests.
- For database constraints, test the durable behavior directly, usually with
  `IntegrityError`.
- For `clean()`, test the explicit validation path you added.
- For selector-owned computation, test the selector instead of re-implementing
  relational logic on the model.
- A new field or relation needs a migration: `just manage makemigrations`.

## Verification

- targeted `pytest` for the files you touched
- `just manage makemigrations --check --dry-run` when models changed
- `git diff --check`

## References

- `docs/2-architecture/service-layer.rst` — where logic belongs, and the model
  property exception
- `docs/2-architecture/module-boundaries.rst` — the cross-module relation policy
- `docs/3-backend-guides/migrations.rst`
- `docs/adr/0009-cross-module-foreign-keys-by-justification.md`
- `platform_django/users/models.py` and `platform_django/users/tests/test_models.py`
