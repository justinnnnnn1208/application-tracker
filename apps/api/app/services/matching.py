"""Local, explainable preference scoring; never immigration or application eligibility."""
import hashlib
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db.models import Fact, JobRequirements, MatchResult, Preferences, Profile, now
from app.services.requirements import validated as validated_requirements
from app.services.errors import NeedsInput

VERSION = "preference-v6-explicit-new-grad"
WEIGHTS = {"role": 20, "graduate": 25, "location": 20, "skills": 20, "experience": 10, "start_date": 5}
SKILLS = ("python", "java", "javascript", "typescript", "c++", "c#", "rust", "golang", "sql", "react", "linux", "docker", "kubernetes", "terraform", "pytorch", "tensorflow", "aws", "azure", "git")


def contains(text, term):
    return bool(re.search(r"(?<![\w+#])" + re.escape(term) + r"(?![\w+#])", text, re.I))


def immigration_term(value):
    # Exclude these job-text candidates, never evaluate a person's legal status.
    value = re.sub(r"[_/\-\u2010-\u2015]+", " ", value)
    return bool(re.search(
        r"\b(?:visas?|sponsor(?:ship|ing|ed|s)?|immigration|citizenship|nationality|ILR|EUSS|"
        r"(?:indefinite|limited|permanent)\s+leave\s+to\s+(?:remain|enter)|permanent\s+residen(?:cy|ce|t)|"
        r"(?:pre\s*)?settled\s+status|EU\s+settlement\s+scheme|(?:authori[sz]ed|eligible)\s+to\s+work|"
        r"work(?:ing)?\s+rights|skilled\s+worker|work\s+(?:permits?|authori[sz]ation|eligibility)|"
        r"right\s+to\s+work|permission\s+to\s+work)\b", value, re.I))


def graduate_level(title, description):
    # Explicit role level, not eligibility of any individual or boilerplate benefits.
    if re.search(r"\b(senior|staff|lead|manager|director|principal|head)\b", title, re.I):
        return "NO"
    if re.search(r"\bintern(?:ship)?\b", title, re.I):
        return "UNVERIFIED"
    if re.search(r"\b(?:graduate|junior|new[\s-]+grad)\b", title, re.I):
        return "YES"
    if re.search(r"\b[3-9](?:\s*[-–]\s*\d+)?\+?\s+years\b.{0,45}\bexperience\b", description, re.I):
        return "NO"
    return "UNVERIFIED"


def shared_inputs(session):
    profile = session.get(Profile, 1)
    preferences = session.get(Preferences, 1)
    facts = session.scalars(select(Fact).where(Fact.verified.is_(True)).order_by(Fact.id)).all()
    analyses = {row.job_id: row for row in session.scalars(select(JobRequirements))}
    return {"version": VERSION, "analyses": analyses,
            "locations": profile.target_locations if profile else "", "graduation_year": profile.graduation_year if profile else None,
            "roles": preferences.target_roles if preferences else [], "weights": preferences.weights if preferences and preferences.weights else WEIGHTS,
            "facts": [{"id": fact.id, "category": fact.category, "content": fact.content} for fact in facts]}


def inputs(session, job, shared=None):
    job_data = {key: getattr(job, key) for key in ("title", "company", "location", "description", "start_date", "eligibility_requirements")}
    job_data["description"] = job.description or job.notes
    job_data["source_kind"] = "vacancy" if job.description else "notes_summary" if job.notes else "missing"
    context = shared if shared is not None else shared_inputs(session)
    row = context["analyses"].get(job.id)
    validated = validated_requirements(job, row)
    requirements = validated.model_dump() if validated is not None else None
    return {**{key: value for key, value in context.items() if key != "analyses"}, "job": job_data, "requirements": requirements}


def active_for_matching(job, application):
    if application.status not in {"DISCOVERED", "SHORTLISTED"}:
        return False
    if application.status == "DISCOVERED" and (job.tracker_status or "").strip().casefold() in {"applied", "rejected", "offer", "withdrawn"}:
        return False
    return job.deadline is None or job.deadline >= datetime.now(ZoneInfo("Europe/London")).date()


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def calculate(data):
    job, weights = data["job"], data["weights"]
    title, text = job["title"], job["description"] + "\n" + job["eligibility_requirements"]
    breakdown = []
    def add(field, fraction, explanation, fact_ids=None):
        breakdown.append({"criterion": field, "points": round(weights[field] * fraction, 2), "maximum": weights[field], "explanation": explanation, "fact_ids": fact_ids or []})
    roles = data["roles"] or ["software", "data", "machine learning", "technology", "cloud", "linux", "security", "devops", "firmware", "hardware", "UX", "AI"]
    hits = [term for term in roles if contains(title, term)]
    add("role", bool(hits), "Title matches: " + ", ".join(hits) if hits else "No configured role term found in the title; review manually.")
    level = graduate_level(title, text)
    add("graduate", level == "YES", {"YES": "Explicit graduate/junior/new-grad title.", "NO": "Senior/leadership title or an explicit 3+ years experience requirement.", "UNVERIFIED": "Graduate level is not established; no personal eligibility inferred."}[level])
    targets = [item.strip() for item in re.split(r"[,;\n]", data["locations"]) if item.strip()]
    uk = bool(re.search(r"\b(UK|United Kingdom|England|Scotland|Wales|Northern Ireland|London|Manchester|Leeds|Bristol|Cambridge|Cardiff|Edinburgh|Glasgow|Belfast)\b", job["location"], re.I))
    preferred = [target for target in targets if contains(job["location"], target)]
    add("location", 1 if preferred or (not targets and uk) else .5 if uk else 0, "Preferred location appears in source: " + ", ".join(preferred) if preferred else "Explicit UK location; preferred-city match not established." if uk else "UK/preferred location not established; worldwide/EMEA is not assumed UK-eligible.")
    analysis = data.get("requirements")
    required = {term["value"] for term in analysis["skills"] if not immigration_term(term["value"])} if analysis is not None else {term for term in SKILLS if contains(text, term)}
    for field, categories in [("skills", {"skill", "education", "project", "experience"}), ("experience", {"experience"})]:
        evidence = {term: [fact["id"] for fact in data["facts"] if fact["category"] in categories and contains(fact["content"], term)] for term in required}
        matched = sorted(term for term, ids in evidence.items() if ids)
        ids = sorted({id for term in matched for id in evidence[term]})
        add(field, len(matched) / len(required) if required else 0, f"Reviewed fact overlap: {', '.join(matched) or 'none'}; {len(matched)}/{len(required)} source technologies ({"local extraction" if analysis is not None else "finite-keyword fallback"}). Keyword overlap is not proof of proficiency." if required else "No recognised source technologies; this criterion needs review.", ids)
    start, year = job["start_date"], data["graduation_year"]
    add("start_date", bool(start and year and start.year >= year), f"Source start year {start.year} is not before profile graduation year {year}; month/day availability still needs review." if start and year and start.year >= year else "Start date or graduation year is unknown, or the role starts earlier; review availability.")
    return {"score": round(sum(item["points"] for item in breakdown)), "breakdown": breakdown, "graduate": level}


def ready(job):
    return job.title != "Role not provided" and bool(job.description.strip() or job.eligibility_requirements.strip() or job.notes.strip())


def save_match(session, job, shared=None, commit=True):
    if not ready(job):
        raise NeedsInput("Add the role title and vacancy description before calculating a preference match.")
    data = inputs(session, job, shared)
    result = calculate(data)
    row = session.get(MatchResult, job.id) or MatchResult(job_id=job.id)
    digest = fingerprint(data)
    if row.inputs_hash != digest:
        row.feedback = None
    row.score, row.breakdown, row.inputs_hash = result["score"], result["breakdown"], digest
    row.created_at = now()
    session.add(row)
    if commit:
        session.commit()
    return result
