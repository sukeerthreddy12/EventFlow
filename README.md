# EventFlow

Event registration platform for organisers and attendees — individual and group sign-ups, capacity-aware waitlists, tickets/check-in, and email notifications.

## Stack

| Layer | Tech |
|-------|------|
| API | Django 6 + Django REST Framework |
| Auth | JWT (SimpleJWT) with refresh rotation |
| DB | PostgreSQL |
| Cache / tokens | Redis |
| Async jobs | Celery + Celery Beat (planned) |
| Frontend | React (planned) |

## Apps

| App | Role | Status |
|-----|------|--------|
| `accounts` | Users, roles, auth, email verify, password reset | **Done** |
| `events` | Organiser event lifecycle (draft → published → completed/cancelled) | Planned |
| `registrations` | Individual + team registration, capacity, waitlist | Planned |
| `tickets` | UUID tickets, check-in | Planned |
| `notifications` | Celery emails (confirm, waitlist, cancel, reminders) | Planned |
| `analytics` | Stats, revenue, ops views | Planned |

### Roles

`ADMIN` · `ORGANISER` · `ATTENDEE`

---

## What’s built (`accounts`)

- Custom `User` model with role field
- Register → verification email (Redis token, 15‑min TTL)
- Login → JWT access + refresh; refresh token rotation
- Password reset (single-use Redis token)
- Role permission classes: `IsAdmin`, `IsOrganiser`, `IsAttendee`

---

## What’s coming

### Events (organiser-facing)
Create and manage events with capacity and pricing. Lifecycle: **DRAFT → PUBLISHED → ONGOING → COMPLETED / CANCELLED**. Soft delete, cancel-with-refund flag, and admin override for platform-wide suppress/feature.

### Registrations
Seat locking with `select_for_update()` under Postgres, waitlist when full, auto-promotion on cancel, and a hard unique constraint (one active registration per user per event). Group/team registration reserves multiple seats in one go.

### Tickets & check-in
UUID ticket per confirmed registration. Idempotent check-in (second scan returns success, not an error).

### Notifications
Celery workers for confirmation, waitlist, cancellation, and 24‑hour reminders. Separate worker + beat processes; failed-send retry queue.

### Admin / analytics
Per-event registration counts, check-in rate, waitlist depth, and organiser revenue summaries — plus Django admin for ops.

### Cross-cutting
Structured DRF errors, pagination, CORS for React, UTC timezone discipline, and permission tests on every endpoint.

---

## Hard problems (design focus)

1. **Seat locking** — concurrent registration must be race-safe on Postgres  
2. **Waitlist promotion** — same transaction as cancel; clear rule for team-sized blocks  
3. **JWT refresh** — rotation + frontend interceptor without retry loops  
4. **Idempotent check-in** — atomic check-and-update  
5. **Celery reliability** — retries and silent failure if worker/beat aren’t running  

---

## Local setup (backend)

```bash
# from repo root
uv sync

cd backend
# copy/create .env (never commit it) — see required vars below
docker compose up -d          # Postgres, Redis, pgAdmin
uv run python manage.py migrate
uv run python manage.py runserver
```

### Required `.env` (example names only)

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
├── backend/          # Django project
│   ├── accounts/     # auth & users (shipped)
│   ├── backend/      # settings, urls
│   └── docker-compose.yaml
├── Frontend/         # React (coming)
├── pyproject.toml
└── README.md
```
