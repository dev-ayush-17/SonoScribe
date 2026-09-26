# SonoScribe — Patterns & Conventions

## Commands

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest                          # Run tests
alembic upgrade head            # Run migrations
```

### Frontend
```bash
cd frontend
npm install
npm run dev                     # Dev server on :5173
npm run build                   # Production build
npm test                        # Run tests
```

## Code Conventions

### Python (Backend)
- **Type hints** on all function signatures
- **Pydantic** models for request/response validation
- **Dependency injection** via FastAPI `Depends()`
- **Async** handlers and database operations
- **Provider pattern**: Abstract base class → concrete implementations
- **Config**: All from environment via `pydantic-settings`
- **Imports**: stdlib → third-party → local, separated by blank lines
- **Naming**: snake_case for functions/variables, PascalCase for classes

### TypeScript (Frontend)
- **Strict TypeScript** — no `any` unless truly necessary
- **Functional components** with hooks
- **Named exports** preferred
- **API calls** centralized in `services/` directory
- **Types** in dedicated `types/` directory
- **CSS Modules** or vanilla CSS (no Tailwind unless requested)

### API Design
- REST endpoints under `/api/v1/`
- WebSocket at `/ws/transcript/{meeting_id}`
- Consistent error responses: `{"detail": "message"}`
- Health check at `/api/v1/health`

### Testing
- **Backend**: pytest + pytest-asyncio, httpx for API tests
- **Frontend**: Vitest + Testing Library
- **Fixtures**: Use recorded audio fixtures, mock providers
- **No live API/meeting required** for test suite

### Git
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
- Small, reviewable increments
- No secrets in commits
- `.env.example` always updated
