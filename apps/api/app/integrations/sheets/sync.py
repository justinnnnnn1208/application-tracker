from collections import Counter
from datetime import datetime
import hashlib
import json

from sqlalchemy import select
from app.db.models import Application, ApplicationEvent, Job, SheetLink
from app.schemas import JobData
from app.integrations.sheets.oauth import write_enabled
from app.services.errors import NeedsInput
from app.services.jobs import ensure_job
from app.services.urls import canonical_url

DEFAULT_MAPPING = {"company": "Company", "deadline": "Deadline", "url": "Application Link", "status": "Status", "notes": "Notes"}
SOURCE_STATUSES = {"not started": "DISCOVERED", "discovered": "DISCOVERED", "shortlisted": "SHORTLISTED", "skipped": "SKIPPED", "expired": "EXPIRED", "withdrawn": "WITHDRAWN"}
DISPLAY_STATUSES = {"DISCOVERED": "Not Started", "SHORTLISTED": "Shortlisted", "SKIPPED": "Skipped", "EXPIRED": "Expired", "WITHDRAWN": "Withdrawn"}


def digest(values, formulas):
    return hashlib.sha256(json.dumps([values, formulas], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def at(values, index):
    return str(values[index]) if index < len(values) and values[index] is not None else ""


def deadline(value):
    if value.strip() in {"", "-"}:
        return None
    for format in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), format).date()
        except ValueError:
            pass
    raise ValueError("Unrecognised deadline")


def db_values(session, job):
    application = session.scalar(select(Application).where(Application.job_id == job.id))
    return {"url": job.url, "company": job.company, "title": job.title, "location": job.location,
            "deadline": job.deadline.strftime("%d/%m/%Y") if job.deadline else "",
            "status": DISPLAY_STATUSES[application.status], "sponsorship": job.sponsorship}


def set_status(session, job, new):
    application = session.scalar(select(Application).where(Application.job_id == job.id))
    if application.status != new:
        session.add(ApplicationEvent(application_id=application.id, from_status=application.status, to_status=new))
        application.status = new


def import_sheet(session, config, sheet, write=False):
    if write and not write_enabled(config.spreadsheet_id):
        raise NeedsInput("Sheet write-back is disabled for this copy.")
    values, formulas = sheet.read()
    if len(values) < config.header_row:
        raise NeedsInput("The configured header row was not found in the test copy.")
    headers = [str(value).strip() for value in values[config.header_row - 1]]
    columns = {}
    for field, header in config.mapping.items():
        if headers.count(header) != 1:
            raise NeedsInput("A mapped header is missing or duplicated. Correct the header mapping before syncing.")
        columns[field] = headers.index(header)
    if not {"url", "company"} <= columns.keys():
        raise NeedsInput("Map the Company and Application Link headers before importing.")
    if write and "status" not in columns:
        raise NeedsInput("Map the Status header before write-back.")
    url_counts = Counter()
    for row in values[config.header_row:]:
        try:
            url_counts[canonical_url(at(row, columns["url"]))] += 1
        except ValueError:
            pass
    links = {link.row_number: link for link in session.scalars(select(SheetLink).where(SheetLink.spreadsheet_id == config.spreadsheet_id, SheetLink.tab == config.tab))}
    counts = {"rows_preserved": 0, "jobs_created": 0, "cells_written": 0, "warnings": 0}
    seen_job_ids = set()
    for number, row in enumerate(values[config.header_row:], start=config.header_row + 1):
        raw_formula = formulas[number - 1] if number <= len(formulas) else []
        if not any(str(cell).strip() for cell in row) and not any(str(cell).strip() for cell in raw_formula):
            continue
        counts["rows_preserved"] += 1
        link = links.get(number)
        row_hash = digest(row, raw_formula)
        if not link:
            link = SheetLink(spreadsheet_id=config.spreadsheet_id, tab=config.tab, row_number=number, row_hash=row_hash, raw_values=row, raw_formulas=raw_formula, last_db_values={})
            session.add(link)
        # Every row survives, even when it has no usable URL/company or an unsupported status.
        content = {field: at(row, index) for field, index in columns.items()}
        warning = None
        try:
            if not content.get("url") or not content.get("company"):
                raise ValueError("Missing URL/company")
            data = JobData(url=content["url"], company=content["company"], title=content.get("title") or "Role not provided", location=content.get("location", ""), notes=content.get("notes", ""), deadline=deadline(content.get("deadline", "")))
            job, created = ensure_job(session, data)
            counts["jobs_created"] += int(created)
            duplicate = job.id in seen_job_ids or url_counts[job.url] > 1
            seen_job_ids.add(job.id)
            # Ignore an old row-number binding after an owner sorts or moves rows.
            baseline = link.last_db_values if link.job_id == job.id else {}
            if duplicate:
                warning = "Duplicate job URL: row preserved; write-back disabled for this row."
            elif created:
                job.tracker_status = content.get("status") or None
                mapped = SOURCE_STATUSES.get(content.get("status", "").strip().lower())
                if mapped:
                    set_status(session, job, mapped)
                elif content.get("status"):
                    warning = "Original tracker status preserved separately; it does not prove application confirmation."
            elif row_hash != link.row_hash or link.job_id != job.id:
                # Sheet Notes win, including intentional clearing.
                if "notes" in content:
                    job.notes = content["notes"]
                job.tracker_status = content.get("status") or None
                current = db_values(session, job)
                # Pull sheet-only changes. Concurrent DB changes win for managed fields.
                if baseline and current["deadline"] == baseline.get("deadline"):
                    job.deadline = data.deadline
                mapped = SOURCE_STATUSES.get(content.get("status", "").strip().lower())
                if mapped and baseline and current["status"] == baseline.get("status"):
                    set_status(session, job, mapped)
            current = db_values(session, job)
            if write and not duplicate and baseline:
                for field in ("status",):
                    if field not in columns or current[field] == baseline.get(field):
                        continue
                    index = columns[field]
                    # Never overwrite a formula, a moved row, or a concurrently edited cell.
                    if at(raw_formula, index).startswith("="):
                        warning = "A system-managed cell contains a formula; it was left untouched."
                        continue
                    if canonical_url(sheet.cell(number, columns["url"] + 1)) != job.url:
                        raise NeedsInput("Sheet rows moved during sync. No further writes were attempted; import again before syncing.")
                    if str(sheet.cell(number, index + 1, formula=True)) != at(raw_formula, index):
                        raise NeedsInput("A target cell changed during sync. No further writes were attempted; review the test copy.")
                    if current[field] != content.get(field, ""):
                        sheet.write_cell(number, index + 1, current[field])
                        counts["cells_written"] += 1
                        # Capture our write in the private snapshot for repeatability.
                        row = list(row)
                        raw_formula = list(raw_formula)
                        for target in (row, raw_formula):
                            target.extend([""] * max(0, index + 1 - len(target)))
                            target[index] = current[field]
                    baseline = {**baseline, field: current[field]}
            elif not baseline:
                baseline = current
            link.job_id = job.id
            # Preserve pending DB changes when an import, rather than sync, is run.
            link.last_db_values = baseline
        except (ValueError, TypeError):
            warning = "Row preserved but not imported: check its company, HTTP(S) URL and DD/MM/YYYY deadline."
            link.job_id = None
        link.raw_values = list(row)
        link.raw_formulas = list(raw_formula)
        link.row_hash = digest(row, raw_formula)
        link.warning = warning
        counts["warnings"] += int(warning is not None)
        # Persist progress after each row: an uncertain remote write is never blindly replayed.
        session.commit()
    return counts
