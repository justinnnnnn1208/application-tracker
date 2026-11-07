"""Read structured public JobPosting data. No tools or instructions from pages execute."""
from datetime import date
from html.parser import HTMLParser
import json

from app.schemas import JobData
from app.services.errors import NeedsInput


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts = []
        self.text = []
        self.json_script = False
        self.script = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "script":
            self.json_script = attributes.get("type", "").lower() == "application/ld+json"
            self.script = []
        if tag in {"script", "style", "noscript"}:
            self.ignored += 1
        if tag in {"p", "br", "li", "div", "h1", "h2", "section"}:
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag == "script" and self.json_script:
            self.scripts.append("".join(self.script))
            self.json_script = False
        if tag in {"script", "style", "noscript"}:
            self.ignored = max(0, self.ignored - 1)

    def handle_data(self, text):
        if self.json_script:
            self.script.append(text)
        if not self.ignored:
            self.text.append(text)


def plain_html(value):
    if not isinstance(value, str):
        return ""
    parser = PageParser()
    parser.feed(value)
    return "\n".join(line.strip() for line in "".join(parser.text).splitlines() if line.strip())


def parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def postings(value, depth=0):
    if depth > 15:
        return []
    result = []
    if isinstance(value, dict):
        types = value.get("@type", [])
        if "JobPosting" in (types if isinstance(types, list) else [types]):
            result.append(value)
        for key in ("@graph", "mainEntity", "itemListElement", "item"):
            if key in value:
                result.extend(postings(value[key], depth + 1))
    elif isinstance(value, list):
        for child in value[:100]:
            result.extend(postings(child, depth + 1))
    return result


def extract_job(url: str, html: str, provider=None) -> JobData:
    parser = PageParser()
    parser.feed(html)
    found = []
    for script in parser.scripts[:100]:
        try:
            found.extend(postings(json.loads(script)))
        except (ValueError, RecursionError):
            continue
    if len(found) > 1:
        raise NeedsInput("This page contains multiple jobs. Paste the URL of one specific vacancy or add it manually.")
    if not found:
        if provider:
            return provider.extract(url, plain_html(html))
        raise NeedsInput("No complete JobPosting metadata was found. Add the role manually or configure an extraction provider.")
    item = found[0]
    organisation = item.get("hiringOrganization") or {}
    if not isinstance(organisation, dict) or not isinstance(organisation.get("name"), str) or not isinstance(item.get("title"), str):
        raise NeedsInput("The page does not identify a role title and employer. Add or correct them manually.")
    locations = item.get("jobLocation") or []
    if isinstance(locations, dict):
        locations = [locations]
    names = []
    if isinstance(locations, list):
        for location in locations[:20]:
            address = location.get("address", {}) if isinstance(location, dict) else {}
            if isinstance(address, dict):
                names.append(", ".join(dict.fromkeys(str(address[k]) for k in ("addressLocality", "addressRegion", "addressCountry") if isinstance(address.get(k), str))))
    data = {
        "url": url, "title": plain_html(item["title"]), "company": plain_html(organisation["name"]),
        "location": "; ".join(n for n in names if n), "description": plain_html(item.get("description")),
        "deadline": parse_date(item.get("validThrough")), "start_date": parse_date(item.get("jobStartDate")),
        "eligibility_requirements": plain_html(item.get("qualifications")),
    }
    try:
        return JobData.model_validate(data)
    except ValueError:
        raise NeedsInput("Job metadata is incomplete or invalid. Add the role manually and check the listing.") from None
