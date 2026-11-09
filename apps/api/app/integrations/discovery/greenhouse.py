"""Read the official public Greenhouse board API, never application forms."""
import html
import json
import re

from app.schemas import JobData
from app.services.errors import NeedsInput
from app.services.extraction import plain_html
from app.services.fetching import fetch_page


def validate_board(board):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", board):
        raise ValueError("Use only a Greenhouse board slug, not a URL")
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
            location = row.get("location") or {}
            jobs.append(JobData(url=row["absolute_url"], title=plain_html(row["title"]),
                company=plain_html(row.get("company_name")) or "Employer not provided",
                location=location.get("name", "") if isinstance(location, dict) else "",
                description=plain_html(html.unescape(row.get("content") or ""))))
        except (ValueError, KeyError, TypeError):
            invalid += 1
    return jobs, invalid
