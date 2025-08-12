import { test, expect } from '@playwright/test';

test.describe('Admin Storage Config', () => {
  test('affiche la page et éléments principaux (mock API)', async ({ page }) => {
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

  await page.goto('/admin/storage-config');
  await page.waitForSelector('[data-testid="storage-config-title"]');
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

  test('affiche une erreur si la sauvegarde échoue (PUT 500)', async ({ page }) => {
    let putAttempts = 0;
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
        putAttempts++;
        await route.fulfill({
          status: 500,
          contentType: 'text/plain',
          body: 'Boom'
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto('/admin/storage-config');
    await page.waitForSelector('[data-testid="storage-config-backend"]');
    await page.getByTestId('storage-config-backend').selectOption('google_drive');
    await page.getByTestId('storage-config-gdrive-folder').fill('folderERR');
    await page.getByTestId('storage-config-gdrive-json').fill('/secrets/err.json');
    await page.getByRole('button', { name: /enregistrer/i }).click();
    // Le toast d'erreur doit apparaître
    await page.waitForSelector('[data-testid="storage-config-toast"]');
    const toastText = await page.getByTestId('storage-config-toast').innerText();
    expect(toastText.toLowerCase()).toContain('erreur');
    expect(putAttempts).toBe(1);
  });
});
