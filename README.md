# EventFlow

Event registration platform for organisers and attendees — capacity-aware waitlists, tickets/check-in, and (planned) group sign-ups and async email notifications.

**Progress (approx.):** backend core ~65–70% · full product (incl. React) ~45–50%

## Stack

| Layer | Tech | Status |
|-------|------|--------|
| API | Django 6 + Django REST Framework | In use |
| Auth | JWT (SimpleJWT) with refresh rotation + blacklist | Done |
| DB | PostgreSQL | In use |
| Cache / tokens | Redis | In use (verify + password-reset tokens) |
| Docs | drf-spectacular (`/docs/`) | Done |
| Async jobs | Celery + Celery Beat | Planned |
| Frontend | React | Not started |

### Roles

`ADMIN` · `ORGANISER` · `ATTENDEE`

---

## Progress by app

| App | Role | Status |
|-----|------|--------|
| `accounts` | Users, roles, auth, email verify, password reset | **Done** (~95%) |
| `events` | Organiser CRUD, publish/unpublish/cancel, soft delete, admin override | **Core done** (~85%) |
| `registrations` | Individual register, waitlist, cancel + promote | **Core done** (~90%) |
| `tickets` | Auto-issue on confirm, cancel ticket, check-in by token | **Core done** (~95%) |
| `notifications` | Celery emails (confirm, waitlist, cancel, reminders) | **Not started** |
| `analytics` | Stats, revenue, ops APIs | **Not started** |
| Frontend | React UI wired to all APIs | **Not started** |

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
- Create as **DRAFT** (organiser only); list/detail/update own events
- **Publish** / **unpublish** (`DRAFT` ↔ `PUBLISHED`)
- **Cancel** — sets `CANCELLED` + `refund_eligible=True` (bulk notify deferred to Celery)
- **Soft delete** (row kept, hidden from API lists)
- Organiser can only modify their own events
- **Admin override** — `PATCH .../admin-override/` sets `is_featured` / `is_suppressed` (admin only, any event)
- Suppressed events block new registrations

### Registrations (individual)
- `Registration` statuses: `CONFIRMED` / `WAITLISTED` / `CANCELLED`
- `POST /api/registrations/` with `event_id` (attendee/organiser registering for others’ events)
- Seat lock: `select_for_update()` inside `transaction.atomic()` (Postgres)
- Unlimited waitlist when full; promote oldest waitlisted on confirmed cancel (same transaction)
- Partial unique constraint: one **active** registration per user per event (re-register after cancel allowed)
- Concurrency smoke-tested (last seat → one confirmed, one waitlisted)

### Tickets
- One ticket per registration (`OneToOne`); scan `token`
- Auto-issued when registration becomes `CONFIRMED` (register + waitlist promote)
- Ticket cancelled when confirmed registration is cancelled
- `POST /api/tickets/check-in/` with `{ "token": "..." }` — organiser of that event; marks `USED`; idempotent (`USED` → still 200)

### Infra
- Docker Compose: Postgres, Redis, pgAdmin
- Secrets via `backend/.env` (not committed); `DJANGO_SECRET_KEY` from env
- OpenAPI docs tagged: Accounts / Events / Registrations / Tickets

---

## What’s next (priority)

1. **Team / group registration** — multi-seat blocks + waitlist rule for teams
2. **Celery notifications** — confirm, waitlist, promote, cancel, 24h reminders; worker + beat
3. **Frontend (React)** — auth flows, organiser event UI, attendee register, ticket/QR, check-in scanner; CORS
4. **Events leftovers** — derived or scheduled `ONGOING` / `COMPLETED`; public attendee event catalog
5. **Analytics** — regs per event, check-in rate, waitlist depth, organiser revenue
6. **Cross-cutting** — pagination, structured exception handler, broader permission tests

---

## Main API surface (backend)

| Area | Endpoints (summary) |
|------|---------------------|
| Accounts | `register/`, `verify-email/`, `login/`, `token/refresh/`, `password-reset/`, `password-reset-confirm/`, `me/` |
| Events | `GET\|POST /api/events/`, `GET\|PATCH\|DELETE /api/events/<id>/`, `.../publish/`, `.../unpublish/`, `.../cancel/`, `PATCH .../admin-override/` |
| Registrations | `GET\|POST /api/registrations/`, `POST /api/registrations/<id>/cancel/` |
| Tickets | `POST /api/tickets/check-in/` (`token` in body) |

Interactive docs: `http://127.0.0.1:8000/docs/`

---

## Hard problems (status)

| Concern | Status |
|---------|--------|
| Seat locking (Postgres + concurrency) | **Done** for individual regs |
| Waitlist promotion in same transaction as cancel | **Done** |
| Idempotent check-in (by token) | **Done** |
| JWT refresh + FE interceptor (no retry loops) | Backend done; **FE pending** |
| Team-sized waitlist / capacity | **Not started** |
| Celery reliability | **Not started** |

---

## Local setup (backend)

```bash
# from repo root
uv sync

cd backend
# create backend/.env (never commit it) — see vars below
docker compose up -d          # Postgres, Redis, pgAdmin
uv run python manage.py migrate
uv run python manage.py runserver
```

### Required `.env` (placeholder names only)

```env
DJANGO_SECRET_KEY=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

Do **not** commit `backend/.env` or `.venv`.

---

## Repo layout

```
Eventflow/
├── backend/
│   ├── accounts/         # auth & users
│   ├── events/           # organiser events + admin override
│   ├── registrations/    # individual regs + waitlist
│   ├── tickets/          # tickets + check-in
│   ├── backend/          # settings, root urls
│   └── docker-compose.yaml
├── Frontend/             # React (coming)
├── pyproject.toml
└── README.md
```
