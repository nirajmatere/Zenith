import js from "@eslint/js";
import nextPlugin from "@next/eslint-plugin-next";
import tseslint from "typescript-eslint";

export default [
  js.configs.recommended,

  // TypeScript rules (no type-checking needed)
  ...tseslint.configs.recommended,

  // Next.js rules
  {
    plugins: { "@next/next": nextPlugin },
    rules: {
      ...nextPlugin.configs["core-web-vitals"].rules,
    },
  },

  // Ignore build output
  {
    ignores: [".next/**", "node_modules/**", "out/**", "dist/**", "**/*.d.ts"],
  },  
];
