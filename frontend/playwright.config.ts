/// <reference types="node" />
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests-e2e',
  timeout: 30_000,
  // Retry global (chromium fiable) – on compense les navigateurs plus lents avec actionTimeout custom
  retries: 1,
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'NEXT_PUBLIC_DISABLE_AUTH=1 npm run build && NEXT_PUBLIC_DISABLE_AUTH=1 npm run start',
    port: 3000,
    reuseExistingServer: true,
    timeout: 120_000
  },
  // Pas de retries spécifiques par projet dans Playwright; on ajuste actionTimeout pour absorber lenteurs.
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'], actionTimeout: 15_000 } },
    { name: 'webkit', use: { ...devices['Desktop Safari'], actionTimeout: 20_000 } }
  ]
});
