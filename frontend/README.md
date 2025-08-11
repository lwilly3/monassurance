## Monassurance – Frontend (Next.js + TypeScript)

Frontend de l’application Monassurance, basé sur Next.js (App Router) et TypeScript.

### Prérequis
- Node.js 18.x (ou supérieur compatible)

### Installation
```bash
cd frontend
npm install
```

### Démarrage (dev)
```bash
npm run dev
# http://localhost:3000
```

### Build (prod)
```bash
npm run build
npm run start
```

### Lint
```bash
npm run lint
```

### Types OpenAPI
Génère `src/lib/api.types.ts` à partir de l’OpenAPI du backend:
```bash
# Assurez-vous que le backend FastAPI tourne (ex: 127.0.0.1:8000)
BACKEND_URL=http://127.0.0.1:8000 npm run gen:api
```
Le script utilise 127.0.0.1:8000 par défaut si `BACKEND_URL` n’est pas fourni.

### Variables d’environnement
- `NEXT_PUBLIC_API_BASE` (ex: http://127.0.0.1:8000)
	- Copiez `.env.example` vers `.env.local` et adaptez si besoin.
	- Doit pointer vers l’API backend exposant `/api/v1`.

Optionnel pour la génération des types:
- `BACKEND_URL` (par défaut http://127.0.0.1:8000)
	- Utilisé par `npm run gen:api` si vous souhaitez surcharger la cible.

### Auth – résumé
- Le refresh token est stocké en cookie httpOnly (via routes API Next).
- L’access token est gardé côté client en mémoire (et rafraîchi automatiquement sur 401).

Plus de détails: voir `ARCHITECTURE.md`.
