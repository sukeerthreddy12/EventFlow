# concurrency_register_test.py
# Run from backend/:  uv run python registrations/concurrency_register_test.py
# Do not commit real JWT tokens.
import json
import threading
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
EVENT_ID = "c183df65-91b1-453a-b03f-2672444eee43"

TOKENS = [
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg0MzU1MDU1LCJpYXQiOjE3ODQzNTQxNTUsImp0aSI6ImNkMWU0NjNkMzExNzQ5MTM5YjQxODQxZGNhMmE2OGI0IiwidXNlcl9pZCI6IjhlNTIwZDExLTk4MDItNDFlMi1iMmE3LTI4NGE3NjYyYzVkYSJ9.HaZgksWDIf7HD_qKtGf1cgheKWvyywOvrqR347UL-o4",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg0MzU1MDk5LCJpYXQiOjE3ODQzNTQxOTksImp0aSI6IjAxMTYxZDdhMWI1YTRkODk5YWZiZDA1ZGE4ZjNmN2Q2IiwidXNlcl9pZCI6IjcxMjEzNTUzLTM3ODAtNDgwMC05OThmLWUwY2VmODZlZjAzZCJ9.MWXz5ljLnAdOlI67EMzQq0lk9qu-qdmUAHgbJwFFcBY",
]

results = []
lock = threading.Lock()


def register(token):
    data = json.dumps({"event_id": EVENT_ID}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/api/registrations/",
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            with lock:
                results.append((resp.status, body))
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        with lock:
            results.append((e.code, body))


threads = [threading.Thread(target=register, args=(t,)) for t in TOKENS]
for t in threads:
    t.start()
for t in threads:
    t.join()

for status_code, body in results:
    print(status_code, body.get("status"), body)
