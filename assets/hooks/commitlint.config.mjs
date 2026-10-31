// Messages au format Conventional Commits (references/conventions.md).
export default {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Un corps de message en français dépasse vite 100 caractères par ligne : avertir sans bloquer.
    'body-max-line-length': [1, 'always', 100],
  },
};
