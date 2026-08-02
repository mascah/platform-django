/**
 * shadcn/ui and magicui components are vendored verbatim via the shadcn CLI and
 * re-vendored on upgrade, so we lint them for correctness but not for the
 * stylistic/React-Compiler rules that upstream does not satisfy — any local fix
 * is overwritten on the next `shadcn add`.
 *
 * ponytail: path-scoped opt-out, delete entries once upstream satisfies them.
 */
export const vendoredComponentOverrides = [
  {
    files: ['src/components/**', 'src/hooks/**'],
    rules: {
      // eslint core (new in v10)
      'no-useless-assignment': 'off',
      // react-hooks v7 React Compiler rules
      'react-hooks/purity': 'off',
      'react-hooks/immutability': 'off',
      'react-hooks/static-components': 'off',
      'react-hooks/set-state-in-effect': 'off',
      'react-hooks/refs': 'off',
    },
  },
];
