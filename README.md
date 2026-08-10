# EventFlow

Event registration platform for organisers and attendees — capacity-aware waitlists, group sign-ups, tickets/check-in (with QR), organiser analytics, and async email notifications (with Beat reminders + retry queue + event lifecycle).

**Progress (approx.):** backend ~95% · frontend ~95% · full product (deploy + polish) ~90%

## Stack

| Layer | Tech | Status |
|-------|------|--------|
| API | Django 6 + Django REST Framework | In use |
| Auth | JWT (SimpleJWT) with refresh rotation + blacklist | Done |
| DB | PostgreSQL | In use |
| Cache / tokens / broker | Redis | In use (auth tokens + Celery broker) |
| Docs | drf-spectacular (`/docs/`) | Done |
| Async jobs | Celery **worker** + **Beat** | Done (reminders, retry queue, event status advance) |
| Email (dev) | SMTP via **Mailtrap** (env-driven) | Done |
| Frontend | React (Vite) + React Router + Axios | **Done** (Night venue UI, ticket QR, organiser analytics) |
| CORS | `django-cors-headers` → Vite `5173` | Done |

### Roles

`ADMIN` · `ORGANISER` · `ATTENDEE`

---

## Progress by app

| App | Role | Status |
|-----|------|--------|
| `accounts` | Users, roles, auth, email verify, password reset | **Done** (~95%) |
| `events` | Organiser CRUD, publish/unpublish/cancel, soft delete, admin override, public catalog, **Beat `ONGOING`/`COMPLETED`** | **Done** (~95%) |
| `registrations` | Individual + team register, waitlist, cancel + promote, 24h reminder flag | **Done** (~95%) |
| `tickets` | Auto-issue, cancel, check-in, get ticket by registration | **Done** (~95%) |
| `notifications` | Celery emails, Beat 24h reminders, `EmailRetryQueue` | **Done** (~95%) |
| `analytics` | Organiser summary + per-event stats (regs, waitlist, check-in rate, revenue) | **Done** (~95%) |
| Frontend | Auth, catalog, register, tickets + **QR**, organiser CRUD, check-in, **analytics** | **Done** (~95%) |

---

## What’s built

### Accounts
- Custom `User` model with `role`
- Register → verification email (Redis token, TTL)
- Login → JWT access + refresh; refresh rotation + blacklist
- Password reset (single-use Redis token)
- Permission classes: `IsAdmin`, `IsOrganiser`, `IsAttendee` (+ composites as needed)
- `GET /api/accounts/me/`

### Events
- `Event` model (title, description, venue, times, capacity, price, status, organiser)
- Create as **DRAFT** (organiser only); list/detail/update own events (response includes `id`)
- **Publish** / **unpublish** (`DRAFT` ↔ `PUBLISHED`); publish blocked if event has already started/ended
- **Cancel** — sets `CANCELLED` + `refund_eligible=True`; fans out cancel emails via Celery
- **Soft delete** (row kept, hidden from API lists)
- **Public catalog** — `GET /api/events/public/` and `GET /api/events/public/<id>/` (`AllowAny`; published, not deleted, not suppressed)
- Organiser can only modify their own events
- **Admin override** — `PATCH .../admin-override/` sets `is_featured` / `is_suppressed`
- Suppressed events block new registrations
- **Lifecycle (Beat)** — `events.tasks.advance_event_statuses` every minute:
  - past-ended `PUBLISHED` / `ONGOING` / `DRAFT` → `COMPLETED`
  - live `PUBLISHED` (`starts_at ≤ now < ends_at`) → `ONGOING`
  - never auto-publishes drafts; requires Celery **worker** + **Beat**

### Registrations (individual)
- Statuses: `CONFIRMED` / `WAITLISTED` / `CANCELLED`
- `POST /api/registrations/` with `event_id`
- Seat lock: `select_for_update()` inside `transaction.atomic()`
- Waitlist when full; promote on confirmed cancel (same transaction)
- Partial unique constraint: one **active** registration per user per event
- `reminder_sent_at` on registration (for Beat 24h reminders)

### Registrations (team / group)
- `TeamRegistration` — lead, event, `member_count`, `group_token`, status
- `POST /api/registrations/team/` with `event_id` + `member_emails` (existing users)
- All-or-nothing confirm/waitlist; cancel one member → whole team
- Waitlist rule (**FIFO, no skip**): promote oldest party only if free seats ≥ party size

### Tickets
- One ticket per registration; scan `token`
- Auto-issued on `CONFIRMED`; cancelled when registration cancelled
- `GET /api/tickets/by-registration/<registration_id>/` — owner only
- `POST /api/tickets/check-in/` — organiser of that event; idempotent `USED`
- Attendee UI shows **QR** encoding the same check-in `token` (organiser paste/scan → existing check-in API)

### Notifications (Celery)
- Worker + Beat (`backend/celery.py`, broker = Redis)
- Async emails (`transaction.on_commit` + `.delay()`):
  - registration confirmed, waitlist joined, waitlist promoted, event cancelled
  - **24h event reminders** (`dispatch_upcoming_event_reminders` on Beat schedule; idempotent via `reminder_sent_at`)
- **`EmailRetryQueue`** — on SMTP failure, persist row; Beat runs `process_email_retry_queue` with backoff
- Dev email via SMTP env (Mailtrap recommended); keep secrets in `backend/.env`

### Analytics
- Organiser summary: event count, confirmed / waitlisted / checked-in totals, overall check-in rate, total revenue (`price × confirmed`)
- Per-event breakdown: capacity, waitlist depth, check-in rate, revenue
- Auth: organiser-only (`IsOrganiser`); attendees get `403`
- Frontend: `/org/analytics` (KPIs + charts)

### Frontend (`Frontend/`)
- Vite + React + TS; Night venue tokens/CSS
- Auth: register, verify email, login, forgot/reset password, JWT refresh interceptor, role guards
- Attendee: public catalog, event detail (solo + team register), my registrations + cancel, ticket view **with QR**
- Organiser: my events, create/edit draft, publish/unpublish/cancel/soft-delete, check-in by token, **analytics**
- Layouts: public / attendee / organiser

### Cross-cutting
- DRF pagination (`PageNumberPagination`, `PAGE_SIZE=20`)
- Structured exception handler → `{ "detail": "...", "errors": {...}? }`

### Infra
- Docker Compose: Postgres, Redis, pgAdmin
- CORS for `http://localhost:5173`
- Secrets via `backend/.env` (not committed)
- `celerybeat-schedule` is runtime state (gitignored)

---

## What’s next (priority)

1. **Deploy** — Compose / Oracle for Django + Redis + worker + Beat + FE (`DEBUG=False`, secrets, CORS)
2. **Polish** — broader tests (accounts), FE pagination UX, optional camera QR scan on check-in
3. **Docs / demo** — keep seed + Mailtrap happy path ready for live proof of Celery delivery

---

## Main API surface (backend)

| Area | Endpoints (summary) |
|------|---------------------|
| Accounts | `register/`, `verify-email/`, `login/`, `token/refresh/`, `password-reset/`, `password-reset-confirm/`, `me/` |
| Events | `GET\|POST /api/events/`, `GET\|PATCH\|DELETE /api/events/<id>/`, `.../publish/`, `.../unpublish/`, `.../cancel/`, `PATCH .../admin-override/`, **`GET /api/events/public/`**, **`GET /api/events/public/<id>/`** |
| Registrations | `GET\|POST /api/registrations/`, `POST /api/registrations/team/`, `POST /api/registrations/<id>/cancel/` |
| Tickets | `POST /api/tickets/check-in/`, **`GET /api/tickets/by-registration/<id>/`** |
| Analytics | **`GET /api/analytics/organiser/summary/`**, **`GET /api/analytics/events/<id>/`** |

Interactive docs: `http://127.0.0.1:8000/docs/`  
Frontend: `http://localhost:5173`

---

## Hard problems (status)

| Concern | Status |
|---------|--------|
| Seat locking (Postgres + concurrency) | **Done** |
| Waitlist promotion in same transaction as cancel | **Done** (FIFO, no skip for teams) |
| Idempotent check-in (by token) | **Done** |
| JWT refresh + FE interceptor | **Done** |
| Team-sized waitlist / capacity | **Done** |
| Celery Beat 24h reminders | **Done** |
| Email retry queue (failed SMTP) | **Done** |
| Event lifecycle `ONGOING` / `COMPLETED` (Beat) | **Done** |
| Ticket QR → check-in token | **Done** (FE encodes token; same check-in API) |
| Organiser analytics (regs / check-in / revenue) | **Done** |

---

## Local setup

### Backend

```bash
# from repo root
uv sync

cd backend
# create backend/.env (never commit it) — see vars below
docker compose up -d          # Postgres, Redis, pgAdmin
uv run python manage.py migrate
uv run python manage.py runserver
```

### Celery (separate terminals; needed for emails **and** event status advance)

```bash
cd backend
uv run celery -A backend worker -l info --pool=solo
uv run celery -A backend beat -l info
```

(`--pool=solo` is recommended on Windows.)  
Restart the **worker** after adding new `@shared_task` modules so tasks register.

### Frontend

```bash
cd Frontend
npm install
npm run dev
```

### Tests

```bash
cd backend
uv run python manage.py test registrations tickets analytics notifications events
```

Covers register/waitlist/promote, check-in, analytics auth, 24h reminder Beat task, email retry queue, and event lifecycle (`ONGOING`/`COMPLETED`).

### Demo seed

```bash
cd backend
uv run python manage.py seed_demo
```

| Role | Email | Password |
|------|-------|----------|
| Organiser | `organiser@demo.com` | `DemoPass123!` |
| Attendee | `attendee@demo.com` | `DemoPass123!` |
| Teammate | `teammate@demo.com` | `DemoPass123!` |

Featured demo event: **Neon Night Market**. Sign out (or clear localStorage) after a flush/reseed so old JWTs are not reused.

### Required `.env` (placeholder names only)

```env
DJANGO_SECRET_KEY=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/0

FRONTEND_VERIFY_URL=http://localhost:5173/verify-email
FRONTEND_PASSWORD_RESET_URL=http://localhost:5173/reset-password
```

Do **not** commit `backend/.env`, `.venv`, or `celerybeat-schedule*`.

---

## Repo layout

```
Eventflow/
├── backend/
│   ├── accounts/         # auth & users (+ seed_demo)
│   ├── events/           # organiser events + public catalog + admin override + lifecycle Beat task
│   ├── registrations/    # individual + team regs + waitlist
│   ├── tickets/          # tickets + check-in
│   ├── notifications/    # Celery tasks, emails, retry queue, 24h reminders
│   ├── analytics/        # organiser summary + per-event stats
│   ├── backend/          # settings, celery app, root urls, exception handler
│   └── docker-compose.yaml
├── Frontend/             # React (Vite) Night venue UI + analytics
├── pyproject.toml
└── README.md
```
