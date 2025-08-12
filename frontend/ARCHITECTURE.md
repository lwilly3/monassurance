# Frontend – Monassurance (Next.js App Router)

Ce document décrit l’architecture, les conventions et les flux d’authentification du frontend.

## Périmètre
- Framework: Next.js 15 (App Router) + TypeScript
- UI: Tailwind (préconfiguré via `@tailwindcss/postcss`)
- Auth: Refresh token en cookie httpOnly via routes API Next; access token en mémoire (client)
- Typage API: `openapi-typescript` génère `src/lib/api.types.ts` à partir de l’OpenAPI exposé par le backend

## Structure clé
- `src/app/`
  - `page.tsx`: page d’accueil (+ bouton Logout)
  - `login/page.tsx`: page de connexion (formulaire)
  - `api/auth/*`: proxy d’authentification vers le backend
    - `login/route.ts`: POST email/password → set cookie `refresh_token` (httpOnly) et renvoie `access_token`
    - `refresh/route.ts`: POST refresh_token cookie → rotate cookie et renvoie un nouvel `access_token`
    - `logout/route.ts`: POST refresh_token cookie → révoque côté backend et supprime le cookie
- `src/middleware.ts`: protège les pages (redirige vers `/login` si pas de cookie `refresh_token`)
- `src/lib/`
  - `api.ts`: helper `apiFetch` pour appeler le backend public (`NEXT_PUBLIC_API_BASE`)
  - `authClient.ts`: client fetch avec tentative automatique de refresh sur 401 (utilise `/api/auth/refresh`)
  - `api.types.ts`: types générés OpenAPI (ne pas éditer à la main)
- `src/components/LogoutButton.tsx`: bouton de déconnexion (consomme `/api/auth/logout`)

## Flux d’authentification
1. Login (form côté `/login`)
   - Appelle `POST /api/auth/login` avec {email, password}
   - La route API Next forward vers le backend, stocke `refresh_token` en cookie httpOnly, et renvoie `access_token` au client
2. Accès aux pages privées
   - `middleware.ts` exige la présence d’un cookie `refresh_token` pour laisser passer
3. Appels API côté client
   - `authClient.fetch()` ajoute `Authorization: Bearer <access_token>` s’il est présent; sinon,
   - sur 401, tente `POST /api/auth/refresh`, met à jour l’`access_token`, puis rejoue la requête
4. Logout
   - `POST /api/auth/logout` (via route API Next) révoque le refresh token côté backend et supprime le cookie

### Bypass Auth pour tests E2E

Pour les tests Playwright isolant des pages (ex: admin storage-config) sans gérer un vrai flux de connexion, le middleware détecte `process.env.NEXT_PUBLIC_DISABLE_AUTH === '1'` et saute la vérification du cookie `refresh_token`.

- Activation: variable d’environnement dans la config `webServer` Playwright.
- Impact: uniquement côté test; ne pas activer en production/staging.
- Avantage: simplifie les tests UI purs (mock API) et réduit la flakiness liée à l’auth.

## Page Admin – Configuration Stockage

Chemin: `/admin/storage-config`.

Objectif: ajuster dynamiquement le backend de stockage documents (local vs Google Drive).

Implémentation:
- Client component `page.tsx` (directive "use client").
- Hook `useStorageConfig` gère: état, chargement initial (GET), validation minimale, sauvegarde (PUT), drapeaux `loading` / `saving` / `success` / `error`.
  - Stratégie: sauvegarde optimiste (succès affiché d'emblée, rollback + erreur si PUT échoue).
- Champs conditionnels: visibles uniquement si backend = google_drive.
- Feedback: toast (Radix), messages inline, overlay lors du `saving`.
- I18n embarqué minimal (`fr`/`en`) via dictionnaire local.
- Accessibilité: labels explicites, rôles `alert` / `status`, overlay `aria-busy`.
- Sélecteurs tests: `data-testid="storage-config-*"`.

Tests:
- Playwright `tests-e2e/storage-config.spec.ts` mocke GET & PUT `**/api/v1/admin/storage-config`.
- Scénarios couverts: affichage page + mise à jour Google Drive.
- Instrumentation temporaire (logs console / réponses) pour diagnostiquer les échecs initiaux.

Évolutions possibles:
- Optimistic update (mettre à jour l’UI avant réponse) avec rollback si échec.
- Extraction dictionnaire i18n globale.
- Ajout test d’erreur serveur (PUT renvoie 500) pour vérifier le toast erreur.

## Configuration
- `.env.local` recommandé côté frontend:
  - `NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000`
- Génération des types API:
  - `npm run gen:api` (utilise `BACKEND_URL` si défini; par défaut `http://127.0.0.1:8000`)
  - Le fichier généré: `src/lib/api.types.ts`

## Bonnes pratiques
- Ne stockez pas le refresh token côté client (reste en cookie httpOnly côté serveur).
- L’access token peut être gardé en mémoire (éviter `localStorage` si possible).
- Utilisez `authClient.fetch()` pour bénéficier du refresh automatique.
- Pour les appels cross-origin directs depuis le client, préférez `apiFetch` uniquement si les CORS backend sont configurés.

## Maintenance
- Si l’OpenAPI backend change, exécuter `npm run gen:api` et committer le diff.
- CI conseillée: étape qui exécute `gen:api` et échoue s’il y a un diff non committé.
- Mettez à jour `NEXT_PUBLIC_API_BASE` selon vos environnements (dev, staging, prod).

## Dépannage rapide
- Erreur `ECONNREFUSED` sur `gen:api`: vérifier que le backend est lancé sur `127.0.0.1:8000`.
- Redirection vers login alors que vous êtes connecté: vérifiez la présence du cookie `refresh_token` (httpOnly) dans l’onglet Storage.
- 401 persistants: le refresh peut échouer (token expiré/révoqué); reconnectez-vous.
