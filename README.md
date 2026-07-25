# EventFlow

Event registration platform for organisers and attendees — capacity-aware waitlists, group sign-ups, tickets/check-in, and async email notifications.

**Progress (approx.):** backend core ~80–85% · full product (incl. React) ~50–55%

## Stack

| Layer | Tech | Status |
|-------|------|--------|
| API | Django 6 + Django REST Framework | In use |
| Auth | JWT (SimpleJWT) with refresh rotation + blacklist | Done |
| DB | PostgreSQL | In use |
| Cache / tokens / broker | Redis | In use (auth tokens + Celery broker) |
| Docs | drf-spectacular (`/docs/`) | Done |
| Async jobs | Celery worker | **Core done** (Beat + retry queue still planned) |
| Frontend | React | Not started |

### Roles

`ADMIN` · `ORGANISER` · `ATTENDEE`

---

## Progress by app

| App | Role | Status |
|-----|------|--------|
| `accounts` | Users, roles, auth, email verify, password reset | **Done** (~95%) |
| `events` | Organiser CRUD, publish/unpublish/cancel, soft delete, admin override | **Core done** (~85%) |
| `registrations` | Individual + team register, waitlist, cancel + promote | **Core done** (~95%) |
| `tickets` | Auto-issue on confirm, cancel ticket, check-in by token | **Core done** (~95%) |
| `notifications` | Celery emails (confirm, waitlist, promote, event cancel) | **Core done** (~70%) |
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
- **Cancel** — sets `CANCELLED` + `refund_eligible=True`; fans out cancel emails via Celery
- **Soft delete** (row kept, hidden from API lists)
- Organiser can only modify their own events
- **Admin override** — `PATCH .../admin-override/` sets `is_featured` / `is_suppressed` (admin only, any event)
- Suppressed events block new registrations

### Registrations (individual)
- `Registration` statuses: `CONFIRMED` / `WAITLISTED` / `CANCELLED`
- `POST /api/registrations/` with `event_id`
- Seat lock: `select_for_update()` inside `transaction.atomic()` (Postgres)
- Waitlist when full; promote on confirmed cancel (same transaction)
- Partial unique constraint: one **active** registration per user per event

### Registrations (team / group)
- `TeamRegistration` — lead, event, `member_count`, `group_token`, status
- `POST /api/registrations/team/` with `event_id` + `member_emails` (existing users)
- All-or-nothing: whole team `CONFIRMED` or whole team `WAITLISTED`
- Each member gets their own `Registration` (+ `Ticket` if confirmed)
- Cancel any team member’s registration → cancels the **whole team**
- Waitlist rule (**FIFO, no skip**): promote oldest party only if free seats ≥ party size; otherwise stop (do not promote a smaller party behind a large team)

### Tickets
- One ticket per registration (`OneToOne`); scan `token`
- Auto-issued when registration becomes `CONFIRMED` (register + waitlist promote)
- Ticket cancelled when confirmed registration is cancelled
- `POST /api/tickets/check-in/` with `{ "token": "..." }` — organiser of that event; marks `USED`; idempotent (`USED` → still 200)

### Notifications (Celery)
- Worker wired (`backend/celery.py`, broker = Redis)
- Async emails (via `transaction.on_commit` + `.delay()`):
  - registration confirmed
  - waitlist joined
  - waitlist promoted
  - event cancelled (one task per active registrant)
- Console email backend in local/dev — messages appear in the **worker** terminal
- **Not yet:** Celery Beat 24h reminders, `EmailRetryQueue`

### Infra
- Docker Compose: Postgres, Redis, pgAdmin
- Secrets via `backend/.env` (not committed); `DJANGO_SECRET_KEY` from env
- OpenAPI docs tagged: Accounts / Events / Registrations / Tickets

---

## What’s next (priority)

1. **Celery Beat** — 24h event reminders; worker + beat as separate processes
2. **`EmailRetryQueue`** — persist failed sends + reprocess task
3. **Frontend (React)** — auth, organiser/attendee UI, ticket/QR, check-in; CORS
4. **Events leftovers** — `ONGOING` / `COMPLETED`; public attendee event catalog
5. **Analytics** — regs per event, check-in rate, waitlist depth, organiser revenue
6. **Cross-cutting** — pagination, structured exception handler, broader permission tests

---

## Main API surface (backend)

| Area | Endpoints (summary) |
|------|---------------------|
| Accounts | `register/`, `verify-email/`, `login/`, `token/refresh/`, `password-reset/`, `password-reset-confirm/`, `me/` |
| Events | `GET\|POST /api/events/`, `GET\|PATCH\|DELETE /api/events/<id>/`, `.../publish/`, `.../unpublish/`, `.../cancel/`, `PATCH .../admin-override/` |
| Registrations | `GET\|POST /api/registrations/`, `POST /api/registrations/team/`, `POST /api/registrations/<id>/cancel/` |
| Tickets | `POST /api/tickets/check-in/` (`token` in body) |

Interactive docs: `http://127.0.0.1:8000/docs/`

---

## Hard problems (status)

| Concern | Status |
|---------|--------|
| Seat locking (Postgres + concurrency) | **Done** (individual + team size) |
| Waitlist promotion in same transaction as cancel | **Done** (FIFO, no skip for teams) |
| Idempotent check-in (by token) | **Done** |
| JWT refresh + FE interceptor (no retry loops) | Backend done; **FE pending** |
| Team-sized waitlist / capacity | **Done** |
| Celery reliability (Beat + retry queue) | **Partial** — worker emails done; Beat/retry pending |

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

### Celery worker (needed for notification emails)

```bash
cd backend
uv run celery -A backend worker -l info --pool=solo
```

(`--pool=solo` is recommended on Windows.)

### Optional smokes

```bash
cd backend
uv run python registrations/smoke_team_cancel_promote.py
uv run python notifications/smoke_notification_hooks.py
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
│   ├── registrations/    # individual + team regs + waitlist
│   ├── tickets/          # tickets + check-in
│   ├── notifications/    # Celery tasks + email helpers
│   ├── backend/          # settings, celery app, root urls
│   └── docker-compose.yaml
├── Frontend/             # React (coming)
├── pyproject.toml
└── README.md
```
