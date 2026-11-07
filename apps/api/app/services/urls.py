from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING = {"gclid", "fbclid", "msclkid", "lever-source"}


def canonical_url(value: str) -> str:
    try:
        parts = urlsplit(value.strip())
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
            raise ValueError("Use an HTTP(S) job URL without credentials")
        port = parts.port
        host = parts.hostname.lower().encode("idna").decode()
        if ":" in host:
            host = f"[{host}]"
        if port and (parts.scheme, port) not in {("https", 443), ("http", 80)}:
            host += f":{port}"
        query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                       if not k.lower().startswith("utm_") and k.lower() not in TRACKING)
        # Preserve SPA hash routes, which may identify different jobs.
        fragment = parts.fragment if parts.fragment.startswith(("/", "!")) else ""
        return urlunsplit((parts.scheme, host, parts.path or "/", urlencode(query), fragment))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Use a valid HTTP(S) job URL without credentials") from exc
