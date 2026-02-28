Component Library
=================

Overview
--------

The project uses ``@workspace/ui``, a shared component library built on `shadcn/ui <https://ui.shadcn.com/>`_ components. These components are built on `Radix UI <https://www.radix-ui.com/>`_ primitives and styled with `Tailwind CSS <https://tailwindcss.com/>`_.

Unlike traditional component libraries installed as npm packages, shadcn/ui components are copied into your project. This gives you full ownership and the freedom to customize every component to fit your needs.

Package Structure
-----------------

The shared UI package lives in the monorepo at ``packages/ui/``:

.. code-block:: text

    packages/ui/
    ├── src/
    │   ├── components/
    │   │   ├── button.tsx
    │   │   ├── card.tsx
    │   │   ├── dialog.tsx
    │   │   ├── input.tsx
    │   │   └── ...
    │   ├── lib/
    │   │   └── utils.ts          # cn() helper for className merging
    │   └── globals.css            # CSS variables and base styles
    ├── package.json
    └── tsconfig.json

Key files:

- **Components** (``src/components/<name>.tsx``): Individual UI components, each in its own file
- **Utilities** (``src/lib/utils.ts``): The ``cn()`` helper function that merges Tailwind CSS classes using ``clsx`` and ``tailwind-merge``
- **Global styles** (``src/globals.css``): CSS variables for theming, base styles, and Tailwind directives

Usage
-----

Import components from the ``@workspace/ui`` package using direct component paths:

.. code-block:: tsx

    import { Button } from '@workspace/ui/components/button';
    import { Card, CardHeader, CardTitle, CardContent } from '@workspace/ui/components/card';
    import { Input } from '@workspace/ui/components/input';

    function MyFeature() {
      return (
        <Card>
          <CardHeader>
            <CardTitle>Create Item</CardTitle>
          </CardHeader>
          <CardContent>
            <Input placeholder="Item name" />
            <Button variant="default">Save</Button>
          </CardContent>
        </Card>
      );
    }

Styling is done with Tailwind CSS utility classes. Components accept a ``className`` prop for customization:

.. code-block:: tsx

    <Button className="w-full mt-4" variant="outline">
      Full Width Button
    </Button>

The ``cn()`` utility handles class merging safely, resolving Tailwind conflicts:

.. code-block:: jsx

    import { cn } from '@workspace/ui/lib/utils';

    function MyComponent({ className }) {
      return (
        <div className={cn('p-4 rounded-lg bg-background', className)}>
          {/* content */}
        </div>
      );
    }

Adding New Components
---------------------

There are two ways to add new shadcn/ui components:

**Using the shadcn/ui CLI:**

.. code-block:: bash

    # From the packages/ui directory
    npx shadcn@latest add <component-name>

**Manually from the registry:**

1. Browse the `shadcn/ui component registry <https://ui.shadcn.com/docs/components>`_
2. Copy the component source code
3. Create a new file at ``packages/ui/src/components/<component-name>.tsx``
4. Adjust imports to match your project structure

Components are copied into the project, not installed as dependencies. This means:

- You own the code and can modify it freely
- No version conflicts or breaking changes from upstream
- Components are tailored to your project's needs
- You can delete parts you don't need

Theming
-------

Theming is controlled through CSS variables defined in ``globals.css``. This provides a centralized way to manage colors, border radius, and other design tokens.

**CSS Variables:**

.. code-block:: css

    :root {
      --background: 0 0% 100%;
      --foreground: 222.2 84% 4.9%;
      --card: 0 0% 100%;
      --card-foreground: 222.2 84% 4.9%;
      --primary: 222.2 47.4% 11.2%;
      --primary-foreground: 210 40% 98%;
      --secondary: 210 40% 96.1%;
      --secondary-foreground: 222.2 47.4% 11.2%;
      --muted: 210 40% 96.1%;
      --muted-foreground: 215.4 16.3% 46.9%;
      --accent: 210 40% 96.1%;
      --accent-foreground: 222.2 47.4% 11.2%;
      --destructive: 0 84.2% 60.2%;
      --destructive-foreground: 210 40% 98%;
      --border: 214.3 31.8% 91.4%;
      --input: 214.3 31.8% 91.4%;
      --ring: 222.2 84% 4.9%;
      --radius: 0.5rem;
    }

**Dark mode** is supported via CSS classes. Dark mode variables are defined under a ``.dark`` class:

.. code-block:: css

    .dark {
      --background: 222.2 84% 4.9%;
      --foreground: 210 40% 98%;
      /* ... dark mode overrides */
    }

**Tailwind configuration** extends these CSS variables so they can be used as utility classes:

.. code-block:: tsx

    {/* These classes reference CSS variables */}
    <div className="bg-background text-foreground">
      <button className="bg-primary text-primary-foreground rounded-[var(--radius)]">
        Click me
      </button>
    </div>

To customize the theme, edit the CSS variables in ``globals.css``. All components that reference these variables will update automatically.

Key Principles
--------------

1. **Composable primitives**: Components are built on Radix UI primitives, providing accessible, unstyled building blocks that you compose together. Each component handles its own accessibility concerns (keyboard navigation, ARIA attributes, focus management).

2. **Utility-first styling**: Style components using Tailwind CSS utility classes rather than custom CSS. This keeps styles co-located with markup and makes the design system predictable.

3. **Full control**: Since components are copied into your project, you can modify the source directly. Need a Button variant that doesn't exist? Add it. Need to change how Dialog animates? Edit the component file.

4. **Consistent design tokens**: All components reference the same CSS variables for colors, spacing, and radius. Changing a variable updates the entire UI consistently.

5. **Accessible by default**: Radix primitives handle complex accessibility patterns (modals, dropdowns, tabs) so you don't have to implement them manually.

See Also
--------

- `shadcn/ui Documentation <https://ui.shadcn.com/>`_ -- Component reference and examples
- `Radix UI Documentation <https://www.radix-ui.com/>`_ -- Primitive component API reference
- `Tailwind CSS Documentation <https://tailwindcss.com/docs>`_ -- Utility class reference
