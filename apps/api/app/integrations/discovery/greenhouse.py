"""Read the official public Greenhouse board API, never application forms."""
import html
import json
import re
from urllib.parse import urlsplit

from app.schemas import JobData
from app.services.errors import NeedsInput
from app.services.extraction import plain_html, labelled_date, parse_date
from app.services.fetching import fetch_page
from app.services.identity import ats_identity


def validate_board(board):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", board):
        raise ValueError("Use only a board slug, not a URL")
    return board


def read_board(board):
    board = validate_board(board)
    # Shared fetcher enforces explicit host approval, robots, rate and size limits;
    # no redirects, login/anti-bot bypass or retries are introduced by discovery.
    body = fetch_page(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true")
    try:
        payload = json.loads(body)
        rows = payload["jobs"]
        if not isinstance(rows, list) or len(rows) > 2000:
            raise ValueError("Invalid board")
    except (ValueError, TypeError, KeyError):
        raise NeedsInput("The public board returned invalid or oversized job data.") from None
    jobs, invalid = [], 0
    for row in rows:
        try:
            if not isinstance(row, dict) or not row.get("id"):
                raise ValueError("Missing posting identity")
            id = str(row["id"])
            if not re.fullmatch(r"[0-9]{1,30}", id) or int(id) <= 0:
                raise ValueError("Invalid posting identity")
            parts = urlsplit(row["absolute_url"])
            if parts.scheme != "https" or parts.port not in {None, 443}:
                raise ValueError("Unsupported public listing URL")
            if parts.hostname == "greenhouse.io" or (parts.hostname or "").endswith(".greenhouse.io"):
                if ats_identity(row["absolute_url"]) not in {f"greenhouse:{board}:{id}", f"greenhouse-eu:{board}:{id}"}:
                    raise ValueError("Mismatched official board/posting URL")
            # Publisher-supplied custom links remain literal. Their query params
            # never establish an authoritative ATS identity or trigger a fetch.
            location = row.get("location") or {}
            content = row.get("content")
            if content is None:
                content = ""
            if not isinstance(content, str):
                raise ValueError("Malformed vacancy content")
            description = plain_html(html.unescape(content))
            text = " ".join(description.split())
            jobs.append(JobData(url=row["absolute_url"], title=plain_html(row["title"]),
                company=plain_html(row.get("company_name")) or "Employer not provided",
                location=location.get("name", "") if isinstance(location, dict) else "",
                description=description, deadline=parse_date(row.get("application_deadline")) or labelled_date(text, r"Applications? deadline"),
                start_date=labelled_date(text, r"Start date")))
        except (ValueError, KeyError, TypeError, AttributeError):
            invalid += 1
    return jobs, invalid
