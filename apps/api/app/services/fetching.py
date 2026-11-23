import ipaddress
import os
import socket
import re
from time import monotonic, sleep
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx
from app.services.errors import NeedsInput
from app.services.urls import canonical_url

USER_AGENT = "GraduateTracker/0.1"
PROXY_DNS_HOSTS = {"boards-api.greenhouse.io", "job-boards.greenhouse.io"}
BLOCKED = ("linkedin.com", "indeed.com", "indeed.co.uk")
_last_request = {}
_robots_cache = {}
ROBOTS_TTL = 300


def validate_public_url(url: str):
    url = canonical_url(url)
    host = urlsplit(url).hostname
    if any(host == domain or host.endswith("." + domain) for domain in BLOCKED):
        raise NeedsInput("LinkedIn and Indeed fetching is not supported. Enter job details manually.")
    if urlsplit(url).port not in {None, 80, 443}:
        raise NeedsInput("Only standard public HTTP(S) job URLs are supported.")
    try:
        addresses = socket.getaddrinfo(host, None)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("Private address")
    except OSError:
        # Managed proxy resolves these fixed official sources remotely. Never fall
        # back for arbitrary hosts, HTTP, literal/private IPs or a private DNS result.
        if host in PROXY_DNS_HOSTS and urlsplit(url).scheme == "https" and (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")):
            return url
        raise NeedsInput("The job URL must resolve to a public Internet address.") from None
    except ValueError:
        raise NeedsInput("The job URL must resolve to a public Internet address.") from None
    return url


def fetch_page(url: str, *, auth=None) -> str:
    if auth is not None:
        parts = urlsplit(canonical_url(url))
        if parts.scheme != "https" or parts.hostname != "www.reed.co.uk" or parts.port is not None or not re.fullmatch(r"/api/1\.0/(?:search/?|jobs/[0-9]{1,15}/?)", parts.path):
            raise NeedsInput("Credential scope is restricted to the official Reed search/job API.")
    url = validate_public_url(url)
    host = urlsplit(url).hostname
    approved = {value.strip().lower() for value in os.environ.get("URL_FETCH_ALLOWED_HOSTS", "").split(",") if value.strip()}
    if host not in approved:
        raise NeedsInput("Fetching this host is not enabled. Check its terms, approve the host in URL_FETCH_ALLOWED_HOSTS, or paste the page HTML.")
    parts = urlsplit(url)
    origin = (parts.scheme, parts.netloc)
    with httpx.Client(timeout=20, follow_redirects=False, headers={"User-Agent": USER_AGENT}) as client:
        def get(target, limit, request_auth=None, *, metadata=False):
            validate_public_url(target)
            delay = max(0, 5 - (monotonic() - _last_request.get(host, -100)))
            if delay:
                sleep(delay)  # This runs only in the separate worker.
            _last_request[host] = monotonic()
            with client.stream("GET", target, **({"auth": request_auth} if request_auth is not None else {})) as response:
                if response.is_redirect:
                    raise NeedsInput("The page redirects. Verify the destination and paste its direct vacancy URL.")
                if response.status_code in {401, 403, 429}:
                    raise NeedsInput("The site requires login, denies access, or is rate-limiting requests. Use manual entry.")
                response.raise_for_status()
                result = bytearray()
                for chunk in response.iter_bytes():
                    result.extend(chunk)
                    if len(result) > limit:
                        raise NeedsInput("The job page is too large. Use manual entry.")
                text = result.decode("utf-8", errors="replace")
                return (text, response.headers) if metadata else text

        try:
            cached = _robots_cache.get(origin)
            if cached and monotonic() < cached[0]:
                rules = cached[1]
            else:
                robots, headers = get(urljoin(url, "/robots.txt"), 200_000, metadata=True)
                rules = RobotFileParser()
                rules.parse(robots.splitlines())
                ttl = ROBOTS_TTL
                age = headers.get('age', '0')
                age = int(age) if age.isdigit() and len(age) <= 10 else 0
                for directive in headers.get('cache-control', '').lower().split(','):
                    name, _, value = directive.strip().partition('=')
                    if name.strip() in {'no-cache', 'no-store'}:
                        ttl = 0
                    if name.strip() == 'max-age':
                        value = value.strip(' "')
                        ttl = min(ttl, max(0, int(value) - age)) if value.isdigit() and len(value) <= 10 else 0
                if ttl:
                    if len(_robots_cache) >= 32:
                        _robots_cache.pop(next(iter(_robots_cache)))
                    _robots_cache[origin] = (monotonic() + ttl, rules)
            if not rules.can_fetch(USER_AGENT, url):
                raise NeedsInput("robots.txt disallows fetching this job page. Use manual entry.")
            # Honour declared delays in addition to the default per-host delay.
            crawl_delay = rules.crawl_delay(USER_AGENT)
            if crawl_delay:
                if crawl_delay > 60:
                    raise NeedsInput("The site's crawl delay is too long for this workflow. Use manual entry.")
                sleep(crawl_delay)
            return get(url, 1_000_000, auth)
        except NeedsInput:
            raise
        except httpx.HTTPError:
            raise NeedsInput("The public job page or robots.txt could not be fetched. Check access or use manual entry.") from None
