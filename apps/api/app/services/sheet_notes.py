"""Use the owner's literal Sheet Notes as summaries, never invent vacancy text."""
import re

from sqlalchemy import select, update

from app.db.models import Job, SheetLink


def role_from_notes(notes):
    first = re.split(r"\n|\.\s+", notes.strip(), maxsplit=1)[0].strip().rstrip(".")
    if not first or len(first) > 300 or re.match(r"^(check|find|see|contact|apply|verify|sponsorship|visa)\b", first, re.I):
        return None
    if not re.search(r"\b(engineer|engineering|developer|analyst|scientist|consultant|programme|program|graduate|intern)\b", first, re.I):
        return None
    return first



def location_from_notes(notes):
    matches = re.finditer(r"\b(London|Manchester|Leeds|Cambridge|Bristol|Edinburgh|Swansea|Cardiff|Glasgow|Belfast|United Kingdom|UK)\b", notes, re.I)
    locations = {}
    for match in matches:
        locations.setdefault(match[0].casefold(), match[0])
    return ", ".join(locations.values())



def details_updates(job, tracked=None):
    tracked = dict(tracked or {})
    updates, markers = {}, {}
    for field, fallback, value in [("title", "Role not provided", role_from_notes(job.notes) or "Role not provided"), ("location", "", location_from_notes(job.notes))]:
        current = getattr(job, field)
        if current == fallback or tracked.get(field) == current:
            if current != value:
                updates[field] = value
            markers[field] = value
    return updates, markers


def fill_sheet_details(job, tracked=None):
    updates, markers = details_updates(job, tracked)
    for field, value in updates.items():
        setattr(job, field, value)
    return markers


def backfill_sheet_details(session):
    """Idempotent local repair of earlier imports; no Google calls or writes."""
    count = 0
    jobs = session.scalars(select(Job).join(SheetLink, SheetLink.job_id == Job.id).distinct()).all()
    for job in jobs:
        links = session.scalars(select(SheetLink).where(SheetLink.job_id == job.id)).all()
        tracked = {}
        for link in links:
            tracked.update((link.last_db_values or {}).get("_notes_fields", {}))
        values, markers = details_updates(job, tracked)
        if values:
            changed = session.execute(update(Job).where(Job.id == job.id, Job.title == job.title, Job.location == job.location, Job.notes == job.notes).values(**values), execution_options={"synchronize_session": False})
            if not changed.rowcount:
                continue  # Concurrent owner edits win.
            count += 1
        for link in links:
            if (link.last_db_values or {}).get("_notes_fields") != markers:
                link.last_db_values = {**(link.last_db_values or {}), "_notes_fields": markers}
    session.commit()
    return count
