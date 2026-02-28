Migration Safety
================

Awareness of migration operations that can cause issues in production, and patterns to mitigate them.

Operations to Watch
-------------------

These standard Django migration operations can lock tables and cause downtime on large datasets:

**Adding a column with a default:**

.. code-block:: python

    # Can rewrite entire table in older PostgreSQL versions
    migrations.AddField(
        model_name="order",
        name="priority",
        field=models.IntegerField(default=0),
    )

Mitigation: Add the column as nullable first, then set defaults via a data migration.

**Adding an index:**

.. code-block:: python

    # Locks table during index build
    migrations.AddIndex(
        model_name="order",
        index=models.Index(fields=["created_at"], name="order_created_idx"),
    )

Mitigation: Use ``CONCURRENTLY`` via a ``RunSQL`` migration or a library that applies this automatically.

**Adding a NOT NULL constraint:**

.. code-block:: python

    # Scans entire table to verify constraint
    migrations.AlterField(
        model_name="order",
        name="customer_id",
        field=models.IntegerField(),  # Was nullable
    )

Mitigation: Add a check constraint first, validate it, then convert to NOT NULL.

The Expand-Contract Pattern
---------------------------

For complex schema changes (like renaming a column), use expand-contract:

1. **Expand** — Add new structure (backward compatible)
2. **Migrate** — Populate new structure with data
3. **Contract** — Remove old structure after code no longer uses it

Example: Renaming ``customer_id`` to ``user_id``:

**Step 1: Expand**

.. code-block:: python

    migrations.AddField(
        model_name="order",
        name="user_id",
        field=models.IntegerField(null=True, db_index=True),
    )

**Step 2: Migrate data**

.. code-block:: python

    Order.objects.filter(user_id__isnull=True).update(user_id=F("customer_id"))

**Step 3: Update code** to use new column

**Step 4: Contract** (weeks later, after verification)

.. code-block:: python

    migrations.RemoveField(model_name="order", name="customer_id")
