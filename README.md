# Dresscode

Backend API for **Dresscode**, a personal wardrobe assistant. Users catalog clothing with photos, let AI extract structured metadata (category, colors, formality, season, and more), plan upcoming events, and get outfit suggestions that account for weather and occasion.

## What it does

1. **Wardrobe catalog** — Create clothing items manually or upload a photo. Vision AI (Google Gemma) can detect multiple garments in one image and create separate wardrobe entries with rich attributes.
2. **Media library** — Store JPEG/PNG/WebP images per item. Optional background analysis runs when media is linked to a dress.
3. **Events** — Schedule outings (business, casual, formal, outdoor, etc.) with date, time, and a German city for location context.
4. **Outfit suggestions** — For an event, the API builds outfits from the user’s season-appropriate wardrobe. The model can call a **weather tool** (Open-Meteo) for forecast data on the event date and city.

All routes except auth registration/login require a JWT access token.

## Tech stack

| Layer | Choice |
|-------|--------|
| API | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM / models | [SQLModel](https://sqlmodel.tiangolo.com/) |
| Database | SQLite (async via `aiosqlite`) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Auth | JWT (access + refresh), Argon2 passwords |
| AI | [google-genai](https://github.com/googleapis/python-genai) (Gemma vision + tool use) |
| Package manager | [uv](https://docs.astral.sh/uv/) |

## Project structure

```
dresscode-back/
├── main.py                 # FastAPI app entrypoint
├── alembic.ini             # Migration config (default DB: db.sqlite3)
├── migrations/             # Alembic revision scripts
├── pyproject.toml
└── src/
    ├── auth/               # Register, login, refresh, /me
    ├── dress/              # Wardrobe CRUD, analyze, from-image
    ├── event/              # Events, cities, outfit suggestions
    ├── media/              # Upload, list, serve files
    ├── ai/                 # Vision analysis, outfit service, weather tool
    └── core/               # Config, DB session, middleware, pagination
```

Successful JSON responses are wrapped by middleware as `{ "success": true, "data": ... }`. OpenAPI docs at `/docs` are not wrapped.

## Prerequisites

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or another way to install dependencies from `pyproject.toml`
- **Google API key** with access to the configured Gemma model (required for image analysis and outfit suggestions)

## Setup

### 1. Clone and install dependencies

```bash
cd dresscode-back
uv sync
```

### 2. Environment variables

Create a `.env` file in the project root (see `.gitignore`). Minimum for local development:

```env
DB_NAME=db.sqlite3
JWT_SECRET_KEY=change-me-to-a-long-random-string

# Required for AI features
GOOGLE_API_KEY=your-google-api-key
```

Optional variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_ACCESS_EXP_MINUTES` | `30` | Access token lifetime |
| `JWT_REFRESH_EXP_DAYS` | `7` | Refresh token lifetime |
| `EMAIL_VERIFICATION_REQUIRED` | `true` | Require users to verify their email-formatted username before login |
| `EMAIL_VERIFICATION_CODE_EXP_MINUTES` | `15` | Verification code lifetime |
| `EMAIL_VERIFICATION_CODE_LENGTH` | `6` | Number of digits in verification codes |
| `SMTP_HOST` | unset | SMTP server for verification emails; when unset, codes are logged for local development |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USERNAME` | unset | SMTP username |
| `SMTP_PASSWORD` | unset | SMTP password |
| `SMTP_FROM_EMAIL` | `SMTP_USERNAME` or `no-reply@dresscode.local` | Sender address for verification emails |
| `SMTP_USE_TLS` | `true` | Use STARTTLS; set `false` for SMTP over SSL |
| `SMTP_TIMEOUT_SECONDS` | `10` | SMTP network timeout |
| `UPLOAD_DIR` | `uploads` | Directory for stored images |
| `MAX_UPLOAD_BYTES` | `10485760` | Max upload size (10 MB) |
| `GEMMA_MODEL_ID` | `gemma-4-26b-a4b-it` | Vision / outfit model id |
| `AI_AUTO_ANALYZE_ON_UPLOAD` | `true` | Background analyze when media is uploaded with `dress_id` |

Use the same `DB_NAME` as in `alembic.ini` (`db.sqlite3` by default) so migrations and the app share one database file.

### 3. Run database migrations

```bash
uv run alembic upgrade head
```

### 4. Start the API server

```bash
uv run uvicorn main:app --reload
```

The API listens on `http://127.0.0.1:8000` by default.

- Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Register: `POST /auth/register` with email-formatted username and password. A verification code is emailed when verification is enabled.
- Verify email: `POST /auth/verify-email` with username and code.
- Resend verification code: `POST /auth/resend-verification-code` with username and password.
- Swagger OAuth login (for trying protected routes in docs): `POST /auth/login_swagger` with username/password after email verification.

## API overview

| Prefix | Purpose |
|--------|---------|
| `/auth` | Register, login, refresh tokens, change password, current user |
| `/dresses` | Wardrobe items; `POST /dresses/from-image` for photo → AI cataloging; `POST /dresses/{id}/analyze` to re-run vision |
| `/media` | Upload and manage images; `GET /media/{id}/file` serves the binary |
| `/events` | CRUD events; `GET /events/cities` lists supported German cities; `POST /events/{id}/suggest-outfits` generates outfit options |

## Development notes

- Uploaded files and the SQLite database are gitignored (`uploads/`, `*.sqlite3`, `.env`).
- Outfit suggestion needs at least two season-matching wardrobe items with usable metadata.
- Weather lookups use the public [Open-Meteo](https://open-meteo.com/) API (no API key).

## License

Not specified in this repository.
