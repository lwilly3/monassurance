import { test, expect } from '@playwright/test';

test.describe('Admin Storage Config', () => {
  test('affiche la page et éléments principaux (mock API)', async ({ page }) => {
    // Instrumentation diagnostics
    page.on('console', msg => {
      console.log('[browser console]', msg.type(), msg.text());
    });
    page.on('pageerror', err => {
      console.log('[browser error]', err.message, err.stack);
    });
    page.on('response', resp => {
      if (resp.url().includes('/admin/storage-config') || resp.url().includes('/api/v1/admin/storage-config')) {
        console.log('[response]', resp.status(), resp.url());
      }
    });
    // Mock de l'API pour éviter dépendance backend
    await page.route('**/api/v1/admin/storage-config', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
            contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            backend: 'local',
            gdrive_folder_id: null,
            gdrive_service_account_json_path: null,
            updated_at: new Date().toISOString()
          })
        });
      } else if (route.request().method() === 'PUT') {
        const json = await route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            backend: json.backend,
            gdrive_folder_id: json.gdrive_folder_id,
            gdrive_service_account_json_path: json.gdrive_service_account_json_path,
            updated_at: new Date().toISOString()
          })
        });
      } else {
        await route.fallback();
      }
    });

    const response = await page.goto('/admin/storage-config', { waitUntil: 'domcontentloaded' });
    console.log('Navigation status:', response?.status());
    // Attendre soit le titre, soit lever un diagnostic
    try {
      await page.waitForSelector('[data-testid="storage-config-title"]', { timeout: 15000 });
    } catch (e) {
      console.log('Selector wait failed, capturing snapshot…');
      const html = await page.content();
      console.log('--- HTML SNAPSHOT START ---');
      console.log(html.slice(0, 4000));
      console.log('--- HTML SNAPSHOT END ---');
      throw e;
    }
    const titleVisible = await page.getByTestId('storage-config-title').isVisible();
    console.log('Title visible?', titleVisible);
    const backendVisible = await page.getByTestId('storage-config-backend').isVisible();
    console.log('Backend select visible?', backendVisible);
    await expect(page.getByTestId('storage-config-title')).toBeVisible();
    await expect(page.getByTestId('storage-config-backend')).toBeVisible();
  });

  test('met à jour la configuration (PUT)', async ({ page }) => {
    let putPayload: any = null;
    await page.route('**/api/v1/admin/storage-config', async route => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            backend: 'local',
            gdrive_folder_id: null,
            gdrive_service_account_json_path: null,
            updated_at: new Date().toISOString()
          })
        });
      } else if (route.request().method() === 'PUT') {
        putPayload = await route.request().postDataJSON();
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            backend: putPayload.backend,
            gdrive_folder_id: putPayload.gdrive_folder_id,
            gdrive_service_account_json_path: putPayload.gdrive_service_account_json_path,
            updated_at: new Date().toISOString()
          })
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto('/admin/storage-config');
    await page.waitForSelector('[data-testid="storage-config-backend"]');
    // Sélectionner Google Drive
  await page.getByTestId('storage-config-backend').selectOption('google_drive');
  await page.waitForSelector('[data-testid="storage-config-gdrive-folder"]');
  await page.waitForSelector('[data-testid="storage-config-gdrive-json"]');
  await page.getByTestId('storage-config-gdrive-folder').fill('folder123');
  await page.getByTestId('storage-config-gdrive-json').fill('/secrets/sa.json');
    // Soumettre
    await page.getByRole('button', { name: /enregistrer/i }).click();
    // Attendre toast ou message
    await page.waitForTimeout(200); // petite latence pour hydration toast
    await page.waitForSelector('text=Configuration enregistrée', { timeout: 5000 });
    // Assertions sur payload
    expect(putPayload).not.toBeNull();
    expect(putPayload.backend).toBe('google_drive');
    expect(putPayload.gdrive_folder_id).toBe('folder123');
    expect(putPayload.gdrive_service_account_json_path).toBe('/secrets/sa.json');
  });
});
