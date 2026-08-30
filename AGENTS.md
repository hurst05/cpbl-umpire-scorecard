# Repository Guidelines

## Project Structure & Module Organization

- `src/` contains the Vue 3 frontend. `src/main.js` bootstraps the app, `src/App.vue` composes the main view, and reusable UI lives in `src/components/`.
- `server/` contains the FastAPI backend: `app.py` exposes API routes, `analyzer.py` performs strike-zone analysis, `collector.py` fetches CPBL data, and `db.py` handles caching.
- `tests/` contains backend pytest tests such as `tests/test_analyzer.py`.
- `data/` is for local runtime/cache data. `index.html`, `vite.config.js`, and `eslint.config.js` configure the frontend; `pyproject.toml` configures Python tooling.

## Build, Test, and Development Commands

Use Node.js with pnpm 11.9.0, Python 3.12+, and uv.

- `pnpm run setup` — install JavaScript and Python dependencies.
- `pnpm run dev` — run the Vite frontend on `127.0.0.1:5173` and FastAPI on `127.0.0.1:8000`.
- `pnpm run dev:frontend` / `pnpm run dev:backend` — run one service independently.
- `pnpm exec vite build` — create the production frontend bundle in `dist/`.
- `pnpm run test:backend` — run the Python test suite.
- `pnpm run lint:py` and `pnpm run format:py` — check or format backend code with Ruff.
- `pnpm exec eslint .` — lint JavaScript and Vue files.

## Coding Style & Naming Conventions

Follow the existing style: two spaces, single quotes, and no semicolons in JavaScript/Vue; four spaces and a 120-character limit in Python. Name Vue components in PascalCase (`ScorecardSummary.vue`), JavaScript variables/functions in camelCase, Python functions/variables in `snake_case`, and constants in `UPPER_SNAKE_CASE`. Keep imports formatted by Ruff/ESLint.

## Testing Guidelines

Use pytest with files named `tests/test_*.py` and functions named `test_*`. Add focused regression tests for analyzer or API behavior, then run `pnpm run test:backend`. No frontend test framework or coverage threshold is currently configured.

## Commit & Pull Request Guidelines

This repository has no existing commits, so no historical convention is established. Use short imperative subjects, for example `Add strike-zone edge-case tests`. Pull requests should explain the behavior changed, list validation commands, link an issue when applicable, and include screenshots for UI changes.

## Security & Configuration Tips

Keep credentials and local database files out of version control; `data/*.db` and environment-specific files should remain local. Review the permissive CORS and external CPBL data-fetching behavior before deploying beyond localhost.
