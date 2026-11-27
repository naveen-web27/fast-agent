"""API protection: real client IP behind Render's proxy, rate limits, scanner/bot blocking, body size cap and security headers.

Everything is plain ASGI and the standard library. Counters live in this process's memory: they reset on every deploy and
are per instance, which is right for one Render instance. Move them to Redis before running two or more instances.
"""
import hashlib
import json
import re
import time
from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

READ_METHODS = {"GET", "HEAD", "OPTIONS"}


@dataclass(frozen=True)
class Rule:
    """At most `limit` requests per `window` seconds, counted per client IP or per signed-in user."""

    name: str
    limit: int
    window: float
    per: str  # "ip" or "user"


# Paths are relative to the API prefix (/api/v1). Every API request also counts toward API_RULE.
API_RULE = Rule("api", 300, 60, "ip")
WRITE_RULES = (Rule("write-ip", 60, 60, "ip"), Rule("write-user", 30, 60, "user"))
EXEMPT = (re.compile(r"^/health(/db)?$"), re.compile(r"^/payments/webhook$"))
PATH_RULES: tuple[tuple[str | None, re.Pattern, tuple[Rule, ...]], ...] = (
    # Public search and type-ahead: generous, but stops scraping the whole directory.
    ("GET", re.compile(r"^/(profiles|workers|workers/jobs|services/suggest)$|^/locations/"), (Rule("search", 120, 60, "ip"),)),
    # View contact already has a daily limit per user; this stops one IP cycling through many accounts.
    (None, re.compile(r"^/(profiles|workers)/[^/]+/contact$|^/workers/jobs/[^/]+/contact$"), (Rule("contact", 30, 60, "ip"),)),
    # Codes sent by email cost money and can be used to spam someone's inbox.
    ("POST", re.compile(r"^/auth/identities/companies/domain-otp/send$|^/claims/code$"),
     (Rule("send-code-ip", 5, 3600, "ip"), Rule("send-code-user", 5, 3600, "user"))),
    # Guessing codes: email OTPs, worker claim codes, company claims.
    ("POST", re.compile(r"^/auth/identities/companies/domain-otp/verify$|^/workers/claim$|^/claims$"), (Rule("verify-code", 10, 600, "ip"),)),
    ("POST", re.compile(r"^/auth/onboarding$"), (Rule("signup", 10, 3600, "ip"),)),
    ("POST", re.compile(r"^/auth/phone-check$"), (Rule("phone-check", 30, 600, "ip"),)),
    # Personal worker links carry a secret key; limit guessing.
    (None, re.compile(r"^/workers/link(/|$)"), (Rule("worker-link", 60, 60, "ip"),)),
    ("POST", re.compile(r"^/payments/(create-order|verify-payment|checkout)$"), (Rule("payments", 20, 600, "user"),)),
    # Spam: new requests, job posts and hire requests.
    ("POST", re.compile(r"^/requests$"), (Rule("new-request", 20, 3600, "user"),)),
    ("POST", re.compile(r"^/workers/jobs$"), (Rule("new-job", 10, 3600, "user"),)),
    ("POST", re.compile(r"^/workers/[^/]+/hire$"), (Rule("hire", 30, 3600, "user"),)),
)

# Paths only attack scanners ask for. RightConnect has no PHP, WordPress or exposed dotfiles.
PROBE_PATH = re.compile(
    r"(^|/)(\.env|\.git|\.svn|\.hg|\.aws|\.ssh|\.htaccess|\.DS_Store|wp-admin|wp-login\.php|wp-content|wp-includes|"
    r"xmlrpc\.php|phpmyadmin|cgi-bin|server-status|actuator|id_rsa|vendor/phpunit)(/|$)|\.(php|asp|aspx|jsp|cgi)$",
    re.IGNORECASE,
)
SCANNER_AGENT = re.compile(
    r"sqlmap|nikto|nmap|masscan|zgrab|nuclei|wpscan|acunetix|dirbuster|gobuster|ffuf|hydra|netsparker|whatweb|jaeles|fimap",
    re.IGNORECASE,
)


def rules_for(method: str, api_path: str) -> tuple[Rule, ...]:
    """The rate-limit rules for one API call; `api_path` has the /api/v1 prefix removed."""
    if any(pattern.match(api_path) for pattern in EXEMPT):
        return ()
    rules: list[Rule] = [API_RULE]
    if method not in READ_METHODS:
        rules.extend(WRITE_RULES)
    for rule_method, pattern, extra in PATH_RULES:
        if (rule_method is None or rule_method == method) and pattern.search(api_path):
            rules.extend(extra)
    return tuple(rules)


def client_ip(forwarded_for: str | None, peer: str | None, proxy_hops: int) -> str:
    """The caller's IP. Each trusted proxy appends the address it saw to X-Forwarded-For, so with N proxies the client is
    the Nth entry from the right; anything further left was sent by the client and can be faked."""
    if proxy_hops > 0 and forwarded_for:
        entries = [entry.strip() for entry in forwarded_for.split(",") if entry.strip()]
        if len(entries) >= proxy_hops:
            return entries[-proxy_hops]
    return peer or "unknown"


class RateLimiter:
    """Sliding-window log per key. The least recently used keys are dropped past `max_keys`, so memory stays bounded."""

    def __init__(self, max_keys: int = 50_000, clock: Callable[[], float] = time.monotonic):
        self._hits: OrderedDict[str, deque[float]] = OrderedDict()
        self._max_keys = max_keys
        self._clock = clock

    def hit(self, key: str, limit: int, window: float) -> float:
        """Count one request. Returns 0 when allowed, otherwise the seconds until the next request would be allowed."""
        now = self._clock()
        hits = self._hits.get(key)
        if hits is None:
            hits = self._hits[key] = deque()
            if len(self._hits) > self._max_keys:
                self._hits.popitem(last=False)
        else:
            self._hits.move_to_end(key)
        while hits and hits[0] <= now - window:
            hits.popleft()
        if len(hits) >= limit:
            return max(hits[0] + window - now, 0.001)
        hits.append(now)
        return 0.0


class BanList:
    """Temporarily blocks IPs that keep misbehaving (scanner paths, scanner tools, repeated 429s)."""

    def __init__(self, strikes: int = 20, window: float = 600, ban_seconds: float = 900, max_keys: int = 50_000,
                 clock: Callable[[], float] = time.monotonic):
        self._strikes = RateLimiter(max_keys, clock)
        self._banned: OrderedDict[str, float] = OrderedDict()
        self._limit, self._window, self._ban_seconds, self._max_keys = strikes, window, ban_seconds, max_keys
        self._clock = clock

    def banned_for(self, ip: str) -> float:
        until = self._banned.get(ip)
        if until is None:
            return 0.0
        left = until - self._clock()
        if left <= 0:
            del self._banned[ip]
            return 0.0
        return left

    def ban(self, ip: str) -> None:
        self._banned[ip] = self._clock() + self._ban_seconds
        self._banned.move_to_end(ip)
        if len(self._banned) > self._max_keys:
            self._banned.popitem(last=False)

    def strike(self, ip: str) -> None:
        if self._strikes.hit(f"strike:{ip}", self._limit, self._window):
            self.ban(ip)


Scope = dict
Receive = Callable[[], Awaitable[dict]]
Send = Callable[[dict], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


async def _json(send: Send, status: int, detail: str, headers: list[tuple[bytes, bytes]] | None = None) -> None:
    body = json.dumps({"detail": detail}).encode()
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode()),
                    (b"cache-control", b"no-store"), *(headers or [])],
    })
    await send({"type": "http.response.body", "body": body})


def _retry_after(seconds: float) -> list[tuple[bytes, bytes]]:
    return [(b"retry-after", str(max(1, int(seconds + 0.999))).encode())]


class ProtectionMiddleware:
    """Blocks scanners and banned IPs, caps request bodies and applies rate limits before a request reaches FastAPI."""

    def __init__(self, app: ASGIApp, *, api_prefix: str = "/api/v1", proxy_hops: int = 1, max_body_bytes: int = 1_048_576,
                 rate_limits_enabled: bool = True, limiter: RateLimiter | None = None, bans: BanList | None = None,
                 log: Callable[[str], None] | None = None):
        self.app = app
        self.api_prefix = api_prefix.rstrip("/")
        self.proxy_hops = proxy_hops
        self.max_body_bytes = max_body_bytes
        self.rate_limits_enabled = rate_limits_enabled
        self.limiter = limiter or RateLimiter()
        self.bans = bans or BanList()
        self.log = log or (lambda message: None)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
        path: str = scope.get("path", "")
        method: str = scope.get("method", "GET").upper()
        peer = (scope.get("client") or (None,))[0]
        ip = client_ip(headers.get("x-forwarded-for"), peer, self.proxy_hops)

        banned = self.bans.banned_for(ip)
        if banned:
            await _json(send, 403, "Too many suspicious requests from your network. Please try again later.", _retry_after(banned))
            return
        agent = headers.get("user-agent", "")
        if SCANNER_AGENT.search(agent):
            self.bans.ban(ip)
            self.log(f"blocked scanner user-agent ip={ip} path={path}")
            await _json(send, 403, "Forbidden")
            return
        if PROBE_PATH.search(path):
            self.bans.strike(ip)
            await _json(send, 404, "Not Found")
            return

        is_api = path == self.api_prefix or path.startswith(f"{self.api_prefix}/")
        if not is_api:
            await self.app(scope, receive, send)
            return
        api_path = path[len(self.api_prefix):] or "/"
        exempt = not rules_for(method, api_path)
        if not agent.strip() and not exempt:
            # Browsers and the Android app always send one; bare scripts often don't.
            self.bans.strike(ip)
            await _json(send, 403, "Requests without a User-Agent are not accepted.")
            return

        length = headers.get("content-length")
        if length is not None:
            try:
                too_big = int(length) > self.max_body_bytes
            except ValueError:
                await _json(send, 400, "Invalid Content-Length")
                return
            if too_big:
                await _json(send, 413, "Request is too large.")
                return

        if self.rate_limits_enabled:
            authorization = headers.get("authorization", "")
            user_key = hashlib.sha256(authorization.encode()).hexdigest()[:32] if authorization else f"ip:{ip}"
            for rule in rules_for(method, api_path):
                key = f"{rule.name}:{ip if rule.per == 'ip' else user_key}"
                wait = self.limiter.hit(key, rule.limit, rule.window)
                if wait:
                    self.bans.strike(ip)
                    self.log(f"rate limited rule={rule.name} ip={ip} path={path}")
                    await _json(send, 429, "Too many requests. Please slow down and try again shortly.", _retry_after(wait))
                    return

        await self.app(scope, self._capped(receive) if length is None else receive, send)

    def _capped(self, receive: Receive) -> Receive:
        """For bodies sent without Content-Length (chunked): stop reading once the cap is passed."""
        received = 0

        async def wrapped() -> dict:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_body_bytes:
                    return {"type": "http.disconnect"}
            return message

        return wrapped


API_CSP = b"default-src 'none'; frame-ancestors 'none'"
# Pages keep their inline scripts and CDNs, so this only blocks framing, plugins and <base> hijacking.
PAGE_CSP = b"frame-ancestors 'none'; object-src 'none'; base-uri 'self'"
COMMON_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"permissions-policy", b"camera=(), microphone=(), geolocation=(), usb=()"),
    # Google sign-in and Razorpay open pop-ups that must still be able to talk back.
    (b"cross-origin-opener-policy", b"same-origin-allow-popups"),
)


class SecurityHeadersMiddleware:
    """Adds browser security headers. Headers a route already set are kept."""

    def __init__(self, app: ASGIApp, *, api_prefix: str = "/api/v1"):
        self.app = app
        self.api_prefix = api_prefix.rstrip("/")

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path: str = scope.get("path", "")
        is_api = path == self.api_prefix or path.startswith(f"{self.api_prefix}/")
        request_headers = {key.lower(): value for key, value in scope.get("headers", [])}
        https = scope.get("scheme") == "https" or request_headers.get(b"x-forwarded-proto", b"").split(b",")[0].strip() == b"https"

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                present = {key.lower() for key, _ in headers}
                extra = [*COMMON_HEADERS, (b"content-security-policy", API_CSP if is_api else PAGE_CSP)]
                if is_api:
                    # Personal data must not be kept by shared caches or the browser's back/forward cache.
                    extra.append((b"cache-control", b"no-store"))
                if https:
                    extra.append((b"strict-transport-security", b"max-age=31536000"))
                headers.extend((key, value) for key, value in extra if key not in present)
                message = {**message, "headers": headers}
            await send(message)

        await self.app(scope, receive, send_with_headers)
