import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

// ESLint 9 con flat config (reemplaza al antiguo .eslintrc.json). Se fija en 9
// porque los plugins de eslint-config-next (react, import, jsx-a11y) no soportan ESLint 10.
export default defineConfig([
  ...nextVitals,
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts"]),
]);
