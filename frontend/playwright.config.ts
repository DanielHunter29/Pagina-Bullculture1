import { defineConfig, devices } from "@playwright/test";

/**
 * Tests e2e de la tienda (Playwright).
 *
 * Levanta el backend (Django con SQLite efímera + datos demo) y el frontend
 * en modo producción (`next build` + `next start`), y recorre el flujo de
 * compra hasta la redirección a WOMPI (que se intercepta: no sale a internet).
 *
 *   npx playwright install chromium   # solo la primera vez
 *   npm run test:e2e
 *
 * PYTHON: intérprete con las dependencias del backend (por defecto `python`).
 */
const API = "http://127.0.0.1:8000";
const WEB = "http://127.0.0.1:3000";
export const E2E_INTEGRITY_SECRET = "test_integrity_e2e";
const CI = !!process.env.CI;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  forbidOnly: CI,
  retries: 0,
  reporter: CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: WEB,
    trace: "retain-on-failure",
    launchOptions: process.env.PW_CHROMIUM_PATH
      ? { executablePath: process.env.PW_CHROMIUM_PATH }
      : {},
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      cwd: "../backend",
      command: [
        "rm -f e2e.sqlite3",
        "$PYTHON manage.py migrate --noinput",
        "$PYTHON manage.py seed_demo",
        "$PYTHON manage.py runserver 127.0.0.1:8000 --noreload",
      ].join(" && "),
      url: `${API}/api/health/`,
      reuseExistingServer: !CI,
      timeout: 120_000,
      env: {
        PYTHON: process.env.PYTHON || "python",
        DJANGO_SETTINGS_MODULE: "config.settings.dev_sqlite",
        SQLITE_PATH: "e2e.sqlite3",
        CORS_ALLOWED_ORIGINS: WEB,
        FRONTEND_URL: WEB,
        WOMPI_PUBLIC_KEY: "pub_test_e2e",
        WOMPI_INTEGRITY_SECRET: E2E_INTEGRITY_SECRET,
        AXES_ENABLED: "False",
      },
    },
    {
      command: "npm run build && npm run start -- -H 127.0.0.1 -p 3000",
      url: WEB,
      reuseExistingServer: !CI,
      timeout: 300_000,
      env: {
        NEXT_PUBLIC_API_URL: `${API}/api`,
        NEXT_PUBLIC_SITE_URL: WEB,
        NEXT_TELEMETRY_DISABLED: "1",
      },
    },
  ],
});
