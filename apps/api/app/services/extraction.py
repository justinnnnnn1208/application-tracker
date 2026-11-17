"""Read structured public JobPosting data. No tools or instructions from pages execute."""
from datetime import date
from html.parser import HTMLParser
from urllib.parse import urlsplit
from app.services.urls import canonical_url
import json
import re

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




def labelled_date(text, label):
    """An explicit day/month/year next to the label; partial dates stay unknown."""
    months = "January February March April May June July August September October November December".split()
    match = re.search(rf"{label}\s*:?\s*(?:Midnight,?\s*)?(\d{{1,2}})\s*(?:st|nd|rd|th)?\s+(" + "|".join(months) + r")\s+(\d{4})\b", text, re.I)
    if not match:
        return None
    try:
        return date(int(match[3]), next(index for index, month in enumerate(months, 1) if month.casefold() == match[2].casefold()), int(match[1]))
    except ValueError:
        return None


class GreenhouseParser(HTMLParser):
    """Read only the visible job header/description; never the application form."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.capture = None
        self.capture_depth = 0
        self.in_title = False
        self.in_h1 = False
        self.titles = []
        self.heading = []
        self.title = []
        self.location = []
        self.description = []
        self.og_url = None
        self.og_title = None
        self.employers = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "noscript"}:
            self.ignored += 1
        if tag == "img" and attrs.get("alt", "").endswith(" Logo"):
            self.employers.append(attrs["alt"][:-5])
        if tag == "meta" and attrs.get("property") == "og:title":
            self.og_title = attrs.get("content")
        if tag == "meta" and attrs.get("property") == "og:url":
            self.og_url = attrs.get("content")
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.in_h1 = True
            self.heading = []
        if tag == "div":
            self.depth += 1
            classes = attrs.get("class", "").split()
            for field in ("location", "description"):
                if f"job__{field}" in classes and self.capture is None:
                    self.capture, self.capture_depth = field, self.depth
        if self.capture and tag in {"p", "li", "br", "div", "h2", "h3"}:
            getattr(self, self.capture).append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"}:
            self.ignored = max(0, self.ignored - 1)
        if tag == "title":
            self.in_title = False
        if tag == "h1" and self.in_h1:
            self.titles.append("".join(self.heading).strip())
            self.in_h1 = False
        if tag == "div":
            if self.capture_depth == self.depth:
                self.capture = None
            self.depth -= 1
        if self.capture and tag in {"p", "li", "h2", "h3"}:
            getattr(self, self.capture).append("\n")

    def handle_data(self, value):
        if self.ignored:
            return
        if self.in_title:
            self.title.append(value)
        if self.in_h1:
            self.heading.append(value)
        if self.capture:
            getattr(self, self.capture).append(value)

    def job(self, url):
        titles = set(" ".join(value.split()) for value in self.titles)
        if len(titles) != 1 or not self.description or not self.og_url or canonical_url(self.og_url) != canonical_url(url):
            raise ValueError("Incomplete or mismatched public vacancy")
        title = next(iter(titles))
        prefix = f"Job Application for {title} at "
        page_title = " ".join("".join(self.title).split())
        if page_title.startswith(prefix):
            employer = page_title[len(prefix):]
        elif self.og_title and " ".join(self.og_title.split()) == title and len(set(self.employers)) == 1:
            employer = self.employers[0]
        else:
            raise ValueError("Employer is not identified consistently")
        description = "\n".join(line.strip() for line in "".join(self.description).splitlines() if line.strip())
        text = " ".join(description.split())
        return JobData(url=url, title=title, company=employer,
                       location=" ".join("".join(self.location).split()),
                       description=description, deadline=labelled_date(text, r"Applications? deadline"),
                       start_date=labelled_date(text, r"Start date"))


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
        if urlsplit(url).hostname == "job-boards.greenhouse.io":
            try:
                greenhouse = GreenhouseParser()
                greenhouse.feed(html)
                return greenhouse.job(url)
            except ValueError:
                pass
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
