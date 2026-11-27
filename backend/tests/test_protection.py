"""API protection: client IP, rate limits, scanner blocking, body cap and security headers (standard library only)."""
import asyncio
import unittest

from app.core.protection import (
    BanList,
    ProtectionMiddleware,
    RateLimiter,
    SecurityHeadersMiddleware,
    client_ip,
    rules_for,
)


class Clock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def names(rules):
    return {rule.name for rule in rules}


async def call(app, path, method="GET", headers=None, client="1.2.3.4", body=b""):
    """Run one request through an ASGI app; returns (status, headers dict, body, reached_app)."""
    sent = []
    raw = [(key.lower().encode(), value.encode()) for key, value in ({"user-agent": "Mozilla/5.0"} if headers is None else headers).items()]
    scope = {"type": "http", "path": path, "method": method, "headers": raw, "client": (client, 5000), "scheme": "http"}

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    start = next(message for message in sent if message["type"] == "http.response.start")
    body_out = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
    return start["status"], {key.decode(): value.decode() for key, value in start["headers"]}, body_out


class Endpoint:
    """A stand-in for FastAPI that answers 200 and remembers what it got."""

    def __init__(self):
        self.calls = 0
        self.body = b""

    async def __call__(self, scope, receive, send):
        self.calls += 1
        message = await receive()
        self.body = message.get("body", b"") if message["type"] == "http.request" else None
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"application/json")]})
        await send({"type": "http.response.body", "body": b"{}"})


def run(coro):
    return asyncio.run(coro)


class ClientIpTests(unittest.TestCase):
    def test_uses_the_address_the_trusted_proxy_added(self):
        # A client can send its own X-Forwarded-For; Render appends the real address on the right.
        self.assertEqual(client_ip("6.6.6.6, 9.9.9.9", "10.0.0.1", 1), "9.9.9.9")
        self.assertEqual(client_ip("6.6.6.6, 9.9.9.9, 172.16.0.5", "10.0.0.1", 2), "9.9.9.9")

    def test_falls_back_to_the_socket_address(self):
        self.assertEqual(client_ip(None, "127.0.0.1", 1), "127.0.0.1")
        self.assertEqual(client_ip("9.9.9.9", "127.0.0.1", 0), "127.0.0.1")
        self.assertEqual(client_ip("9.9.9.9", "127.0.0.1", 3), "127.0.0.1")


class RuleTests(unittest.TestCase):
    def test_sensitive_endpoints_get_their_own_limits(self):
        self.assertEqual(names(rules_for("GET", "/profiles")), {"api", "search"})
        self.assertEqual(names(rules_for("POST", "/auth/identities/companies/domain-otp/send")),
                         {"api", "write-ip", "write-user", "send-code-ip", "send-code-user"})
        self.assertIn("signup", names(rules_for("POST", "/auth/onboarding")))
        self.assertIn("verify-code", names(rules_for("POST", "/workers/claim")))
        self.assertIn("contact", names(rules_for("POST", "/profiles/abc/contact")))
        self.assertIn("contact", names(rules_for("GET", "/workers/jobs/abc/contact")))
        self.assertIn("new-job", names(rules_for("POST", "/workers/jobs")))
        self.assertNotIn("new-job", names(rules_for("GET", "/workers/jobs")))
        self.assertIn("worker-link", names(rules_for("GET", "/workers/link/me")))

    def test_health_and_payment_webhook_are_not_limited(self):
        self.assertEqual(rules_for("GET", "/health"), ())
        self.assertEqual(rules_for("POST", "/payments/webhook"), ())


class RateLimiterTests(unittest.TestCase):
    def test_sliding_window(self):
        clock = Clock()
        limiter = RateLimiter(clock=clock)
        self.assertEqual([limiter.hit("k", 3, 60) for _ in range(3)], [0.0, 0.0, 0.0])
        self.assertAlmostEqual(limiter.hit("k", 3, 60), 60)
        clock.now += 30
        self.assertAlmostEqual(limiter.hit("k", 3, 60), 30)
        clock.now += 30
        self.assertEqual(limiter.hit("k", 3, 60), 0.0)

    def test_memory_is_bounded(self):
        limiter = RateLimiter(max_keys=2, clock=Clock())
        for key in ("a", "b", "c"):
            limiter.hit(key, 1, 60)
        self.assertEqual(limiter.hit("a", 1, 60), 0.0)  # "a" was dropped, so it starts fresh

    def test_ban_list_bans_after_repeated_strikes_and_expires(self):
        clock = Clock()
        bans = BanList(strikes=3, window=60, ban_seconds=100, clock=clock)
        for _ in range(3):
            bans.strike("1.1.1.1")
        self.assertEqual(bans.banned_for("1.1.1.1"), 0.0)
        bans.strike("1.1.1.1")
        self.assertAlmostEqual(bans.banned_for("1.1.1.1"), 100)
        clock.now += 101
        self.assertEqual(bans.banned_for("1.1.1.1"), 0.0)


class ProtectionMiddlewareTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.endpoint = Endpoint()
        self.app = ProtectionMiddleware(
            self.endpoint, proxy_hops=1, max_body_bytes=100,
            limiter=RateLimiter(clock=self.clock), bans=BanList(strikes=5, window=600, ban_seconds=900, clock=self.clock),
        )

    def test_normal_request_passes(self):
        status, _, _ = run(call(self.app, "/api/v1/profiles"))
        self.assertEqual((status, self.endpoint.calls), (200, 1))

    def test_otp_sending_is_limited_per_ip_with_retry_after(self):
        headers = {"user-agent": "Mozilla/5.0", "x-forwarded-for": "9.9.9.9"}
        statuses = [run(call(self.app, "/api/v1/claims/code", "POST", headers))[0] for _ in range(6)]
        self.assertEqual(statuses, [200] * 5 + [429])
        status, response_headers, body = run(call(self.app, "/api/v1/claims/code", "POST", headers))
        self.assertEqual(status, 429)
        self.assertIn(b"Too many requests", body)
        self.assertGreater(int(response_headers["retry-after"]), 3000)
        # A different visitor is not affected.
        other = {"user-agent": "Mozilla/5.0", "x-forwarded-for": "8.8.8.8"}
        self.assertEqual(run(call(self.app, "/api/v1/claims/code", "POST", other))[0], 200)

    def test_spoofed_forwarded_for_does_not_dodge_the_limit(self):
        for fake in range(6):
            status, _, _ = run(call(self.app, "/api/v1/claims/code", "POST", {"user-agent": "x", "x-forwarded-for": f"7.7.7.{fake}, 9.9.9.9"}))
        self.assertEqual(status, 429)

    def test_scanner_paths_404_and_repeat_offenders_are_banned(self):
        for _ in range(5):
            self.assertEqual(run(call(self.app, "/.env"))[0], 404)
        self.assertEqual(run(call(self.app, "/wp-login.php"))[0], 404)
        status, headers, _ = run(call(self.app, "/api/v1/profiles"))
        self.assertEqual((status, self.endpoint.calls), (403, 0))
        self.assertIn("retry-after", headers)
        self.clock.now += 901
        self.assertEqual(run(call(self.app, "/api/v1/profiles"))[0], 200)

    def test_scanner_tools_are_banned_at_once(self):
        self.assertEqual(run(call(self.app, "/api/v1/profiles", headers={"user-agent": "sqlmap/1.7"}))[0], 403)
        self.assertEqual(run(call(self.app, "/", headers={"user-agent": "Mozilla/5.0"}))[0], 403)

    def test_api_needs_a_user_agent_but_health_and_pages_do_not(self):
        self.assertEqual(run(call(self.app, "/api/v1/profiles", headers={}))[0], 403)
        self.assertEqual(run(call(self.app, "/api/v1/health", headers={}))[0], 200)
        self.assertEqual(run(call(self.app, "/pages/marketplace.html", headers={}))[0], 200)

    def test_large_bodies_are_refused(self):
        big = {"user-agent": "Mozilla/5.0", "content-length": "101"}
        self.assertEqual(run(call(self.app, "/api/v1/requests", "POST", big, body=b"x" * 101))[0], 413)
        self.assertEqual(self.endpoint.calls, 0)
        # Without Content-Length (chunked) the app sees a disconnect instead of the oversized body.
        run(call(self.app, "/api/v1/requests", "POST", {"user-agent": "Mozilla/5.0"}, body=b"x" * 101))
        self.assertIsNone(self.endpoint.body)

    def test_limits_can_be_switched_off(self):
        app = ProtectionMiddleware(self.endpoint, rate_limits_enabled=False, limiter=RateLimiter(clock=self.clock))
        statuses = {run(call(app, "/api/v1/claims/code", "POST"))[0] for _ in range(10)}
        self.assertEqual(statuses, {200})


class SecurityHeaderTests(unittest.TestCase):
    def test_api_and_page_headers(self):
        app = SecurityHeadersMiddleware(Endpoint())
        _, api, _ = run(call(app, "/api/v1/profiles"))
        self.assertEqual((api["x-content-type-options"], api["x-frame-options"], api["cache-control"]), ("nosniff", "DENY", "no-store"))
        self.assertEqual(api["content-security-policy"], "default-src 'none'; frame-ancestors 'none'")
        self.assertNotIn("strict-transport-security", api)
        _, page, _ = run(call(app, "/pages/marketplace.html", headers={"x-forwarded-proto": "https"}))
        self.assertIn("frame-ancestors 'none'", page["content-security-policy"])
        self.assertNotIn("cache-control", page)
        self.assertEqual(page["strict-transport-security"], "max-age=31536000")


if __name__ == "__main__":
    unittest.main()
