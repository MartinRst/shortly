import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "http://127.0.0.1:8000"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=json.dumps(body).encode() if body else None, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=5) as resp:
            return resp.status, resp.read().decode(), dict(resp.headers)
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode(), dict(err.headers)


checks = []


def check(name, ok):
    checks.append({"name": name, "passed": bool(ok)})
    print(("PASS " if ok else "FAIL ") + name)


status, body, _ = call("GET", "/health")
check("health endpoint returns 200", status == 200 and json.loads(body)["status"] == "ok")

status, body, _ = call("POST", "/api/links", {"url": "https://kestra.io/docs"})
check("create a short link", status == 201)
code = json.loads(body).get("code", "") if status == 201 else ""

status, _, headers = call("GET", f"/{code}")
check("short link redirects to the target", status == 307 and headers.get("location") == "https://kestra.io/docs")

status, body, _ = call("GET", f"/api/links/{code}")
check("redirect is counted", status == 200 and json.loads(body)["hits"] == 1)

status, _, _ = call("GET", "/api/links/does-not-exist")
check("unknown code returns 404", status == 404)

passed = sum(c["passed"] for c in checks)
print(json.dumps({"passed": passed, "total": len(checks), "checks": checks}))
sys.exit(0 if passed == len(checks) else 1)
