# Permis de Travail – ترخيص عمل

MVP responsive pour digitaliser les permis de travail de **SNDP / AGIL – AGIL Gaz Radès**. Le frontend utilise React, TypeScript, Tailwind et Vite. L’API utilise FastAPI, SQLAlchemy, SQLite et JWT.

> L’application enregistre les mesures de gaz sans les interpréter. Toute approbation, suspension, reprise et clôture reste une décision humaine explicite.

## Structure

```text
work-permit-mvp/
├── backend/
│   ├── app/              # modèles, auth, règles de workflow et API
│   ├── tests/            # scénario métier end-to-end
│   ├── seed.py           # utilisateurs et permis réalistes
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/        # login, dashboard, assistant, détail, historique
    │   ├── api.ts        # client API JWT
    │   ├── auth.tsx      # session frontend
    │   ├── components.tsx
    │   └── constants.ts
    └── package.json
```

## 1. Démarrer le backend

Prérequis : Python 3.11+.

### Windows PowerShell

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python seed.py
uvicorn app.main:app --reload --port 8000
```

### macOS / Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn app.main:app --reload --port 8000
```

API : http://localhost:8000 — documentation : http://localhost:8000/docs

## 2. Démarrer le frontend

Dans un deuxième terminal, avec Node.js 20+ :

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Sous macOS/Linux, remplacer `copy` par `cp`. Ouvrir http://localhost:5173.

## Comptes de démonstration

Tous utilisent le mot de passe `Demo123!`.

| Rôle | Matricule | Email |
|---|---|---|
| Production | `PROD001` | `production@agil.tn` |
| HSE | `HSE001` | `hse@agil.tn` |
| Prestataire | `PREST001` | `prestataire@agil.tn` |
| Admin | `ADMIN001` | `admin@agil.tn` |

## Variables d’environnement

Backend : `DATABASE_URL`, `JWT_SECRET`. Frontend : `VITE_API_URL`.

En développement, SQLite crée `backend/work_permits.db`. Changez obligatoirement `JWT_SECRET` hors développement.

## Vérifications

```bash
# backend, environnement virtuel activé
pytest -q

# frontend
npm run build
```

## Tester le flux principal

1. Connectez-vous avec `PROD001`.
2. Créez un permis, choisissez **Soudage** : l’étape travaux à chaud apparaît.
3. Complétez les informations, les contrôles, les horaires et envoyez le permis.
4. Déconnectez-vous et connectez-vous avec `HSE001`.
5. Ouvrez le permis dans **À valider**, vérifiez les informations, puis approuvez.
6. Suspendez-le avec un motif, puis reprenez-le.
7. Reconnectez-vous comme Production, ouvrez le permis actif, confirmez les cinq vérifications de fin et terminez les travaux.
8. Reconnectez-vous comme HSE et clôturez le permis.
9. Vérifiez que l’état est **Clôturé** et que chaque action apparaît dans la chronologie.

Pour le rejet, créez et soumettez un autre permis, puis utilisez **Rejeter** avec un motif obligatoire.

## Limites volontaires du MVP

Pas de QR code, PDF, notification, mode hors-ligne avancé, IA, analyse automatique des gaz ou analytics avancés. Le JWT est conservé côté client pour ce MVP séparé Vite/API ; pour une mise en production Internet, privilégier un cookie HttpOnly avec protection CSRF et HTTPS.

## Déploiement recommandé

Architecture de production : **Vercel** pour `frontend/`, **Render** pour `backend/` et **Neon PostgreSQL** pour la base persistante. SQLite reste uniquement destiné au développement local.

### Variables Render

```env
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require
JWT_SECRET=une-valeur-aleatoire-longue-et-secrete
FRONTEND_ORIGIN=https://votre-frontend.vercel.app
```

Build : `pip install -r requirements.txt`

Start : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Le fichier `backend/.python-version` impose Python 3.12 sur Render afin d'éviter la compilation incompatible de `pydantic-core` avec Python 3.14.

### Variable Vercel

```env
VITE_API_URL=https://votre-backend.onrender.com/api
```

Pour le monorepo, définir `frontend` comme **Root Directory** dans Vercel et `backend` comme racine du Web Service Render. Le fichier `frontend/vercel.json` assure que les URL React Router directes sont renvoyées vers `index.html`.
