# Intellex Frontend

Enterprise AI workspace for the Intellex platform — conversational AI, agentic
RAG, ACL-aware document management, and AI observability. Built against the
existing FastAPI backend in the repository root (`app/`). **The backend is not
modified by this frontend.**

## Stack

- Next.js (App Router) · TypeScript (strict) · Tailwind CSS v4
- TanStack Query (server state) · React Hook Form + Zod (forms)
- shadcn-style UI primitives on Radix · Lucide icons · Sonner toasts
- react-markdown + remark-gfm (assistant answers only)

## Getting started

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
```

The backend must be running separately (`uvicorn app.main:app`), with CORS
already configured for `localhost:3000`.

### Environment

`.env.local`:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

The API base URL is centralized in `src/lib/config.ts` — never hardcode it.

## Validation

```bash
npx tsc --noEmit   # types
npm run lint       # eslint
npm run build      # production build
```

## Architecture

```
src/
  app/
    login/               public sign-in
    (shell)/             authenticated shell (guard + sidebar)
      chat/              agentic chat workspace (sessions/messages/history)
      employee/          employee home · documents · retrieval · profile
      admin/             org admin: users · departments · teams · documents ·
                         my-documents · retrieval · observability
      platform/          super admin: organization onboarding
    unauthorized/
  components/
    auth/  layout/  chat/  documents/  users/  departments/  teams/
    retrieval/  observability/  admin/  shared/  ui/
  lib/api/               centralized API client + typed endpoint modules
  providers/             auth + query providers
  types/api.ts           exact mirror of backend schemas/enums
```

## Role model

| Area | EMPLOYEE | ORG_ADMIN | SUPER_ADMIN |
| --- | --- | --- | --- |
| Chat / My Documents / Retrieval / Profile | ✔ | ✔ | ✔ (generic authed endpoints) |
| Users · Departments · Teams · Documents | — | ✔ | — |
| Observability | — | ✔ | ✔ |
| Organization onboarding | — | — | ✔ |

Client-side guards are UX only — the FastAPI backend remains the security
boundary for every request.

## Contract notes (intentional limitations)

- Departments/Teams expose creation only in the current backend; no fabricated
  listing endpoints exist. IDs are shown after creation.
- `POST /chat/sessions/{id}/messages` returns `{query, answer, sources}` — no
  synthetic IDs; history is refetched from `GET .../messages`.
- Feedback is displayed read-only (no mutation endpoint exists).
- Retrieval is a diagnostic playground; it does not produce answers.
- Internal agent reasoning is never rendered; only safe execution metadata
  returned by `/admin/observability/*`.
