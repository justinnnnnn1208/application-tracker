import base64
from datetime import timedelta
import hashlib
import os
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import Field, field_validator, model_validator
from sqlalchemy import select

from app.core.encryption import cipher
from app.db.models import Document, Fact, FactCandidate, OAuthCredential, Preferences, Schedule, SheetConfig, SheetLink, Task, SensitiveDeclaration, new_id, now
from app.integrations.sheets.client import LIVE_SHEET_ID
from app.integrations.sheets.oauth import finish, start, client_settings, write_enabled
from app.integrations.sheets.sync import DEFAULT_MAPPING
from app.routers.tracker import DB, require
from app.schemas import FactData, StrictModel, UtcTimestamp
from app.services.errors import NeedsInput
from app.services.urls import canonical_url

router = APIRouter()
public_router = APIRouter()


class TaskOut(StrictModel):
    id: str
    kind: str
    status: str
    result: dict | None
    message: str | None
    created_at: UtcTimestamp


class URLTask(StrictModel):
    url: str = Field(min_length=1, max_length=2048)
    page_html: str = Field(default="", max_length=1_000_000)

    @field_validator("url")
    @classmethod
    def normalized(cls, value):
        return canonical_url(value)


def enqueue(session, kind, payload):
    item = Task(kind=kind, payload=payload)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.get("/tasks", response_model=list[TaskOut])
def tasks(session: DB):
    return session.scalars(select(Task).order_by(Task.created_at.desc(), Task.id).limit(100)).all()


@router.post("/tasks/extract", response_model=TaskOut, status_code=202)
def extract(data: URLTask, session: DB):
    return enqueue(session, "extract_url", data.model_dump())


class Upload(StrictModel):
    format: Literal["txt", "pdf", "docx"]
    content_base64: str = Field(min_length=1, max_length=7_000_000)
    parent_id: str | None = None


class DocumentOut(StrictModel):
    id: str
    parent_id: str | None
    format: str
    sha256: str
    created_at: UtcTimestamp


@router.get("/documents", response_model=list[DocumentOut])
def documents(session: DB):
    return session.scalars(select(Document).order_by(Document.created_at.desc())).all()


@router.post("/documents", response_model=TaskOut, status_code=202)
def upload(data: Upload, session: DB, request: Request):
    try:
        content = base64.b64decode(data.content_base64, validate=True)
    except ValueError:
        raise HTTPException(422, "Invalid file encoding") from None
    if len(content) > 5_000_000:
        raise HTTPException(413, "CV uploads must be under 5 MB")
    if data.parent_id:
        require(session, Document, data.parent_id)
    digest = hashlib.sha256(content).hexdigest()
    existing = session.scalar(select(Document).where(Document.sha256 == digest, Document.format == data.format, Document.parent_id == data.parent_id))
    if not existing:
        existing = Document(id=new_id(), parent_id=data.parent_id, format=data.format, sha256=digest)
        directory = request.app.state.settings.storage_dir / "documents"
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (directory / existing.id).open("xb") as file:
            file.write(content)
        (directory / existing.id).chmod(0o600)
        session.add(existing)
        session.commit()
    return enqueue(session, "parse_cv", {"document_id": existing.id})


@router.get("/documents/{id}/download")
def download(id: str, session: DB, request: Request):
    document = require(session, Document, id)
    file = request.app.state.settings.storage_dir / "documents" / document.id
    if not file.is_file():
        raise HTTPException(404, "Document file is unavailable")
    return FileResponse(file, filename=f"cv-{document.id}.{document.format}", media_type="application/octet-stream")


class CandidateOut(StrictModel):
    id: str
    document_id: str
    content: str
    category: str | None
    fact_id: str | None
    decision: str


@router.get("/candidates", response_model=list[CandidateOut])
def candidates(session: DB):
    return session.scalars(select(FactCandidate).where(FactCandidate.decision == "PENDING").order_by(FactCandidate.id)).all()


class DeclarationData(StrictModel):
    category: Literal["right_to_work", "sponsorship", "convictions", "disability", "diversity", "consent", "identity"]
    question: str = Field(min_length=1, max_length=500)
    value: str = Field(min_length=1, max_length=2000)
    confirmed: Literal[True]


@router.get("/declarations")
def declarations(session: DB):
    return [{"id": d.id, "category": d.category, "question": d.question, "value": d.value, "confirmed": d.confirmed} for d in session.scalars(select(SensitiveDeclaration).order_by(SensitiveDeclaration.id))]


@router.post("/declarations", status_code=201)
def save_declaration(data: DeclarationData, session: DB):
    item = SensitiveDeclaration(**data.model_dump())
    session.add(item)
    session.commit()
    return {"id": item.id}


@router.delete("/declarations/{id}", status_code=204)
def remove_declaration(id: str, session: DB):
    session.delete(require(session, SensitiveDeclaration, id))
    session.commit()


@router.post("/candidates/{id}/accept")
def accept_candidate(id: str, data: FactData, session: DB):
    candidate = require(session, FactCandidate, id)
    if candidate.decision != "PENDING":
        raise HTTPException(409, "This candidate has already been reviewed")
    fact = Fact(category=data.category, content=data.content, source=f"CV document {candidate.document_id}", verified=data.verified)
    session.add(fact)
    session.flush()
    candidate.fact_id, candidate.decision = fact.id, "ACCEPTED"
    session.commit()
    return {"fact_id": fact.id}


@router.post("/candidates/{id}/reject", status_code=204)
def reject_candidate(id: str, session: DB):
    candidate = require(session, FactCandidate, id)
    if candidate.decision != "PENDING":
        raise HTTPException(409, "This candidate has already been reviewed")
    candidate.decision = "REJECTED"
    session.commit()


class PreferencesData(StrictModel):
    backup_dir: str = Field(default="", max_length=2048)
    target_roles: list[str] = Field(default_factory=list, max_length=30)
    weights: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_values(self):
        if self.backup_dir and not Path(self.backup_dir).expanduser().is_absolute():
            raise ValueError("Use an absolute backup destination")
        allowed = {"skills", "graduate", "start_date", "role", "location", "experience"}
        if not self.weights.keys() <= allowed or any(not 0 <= n <= 100 for n in self.weights.values()):
            raise ValueError("Invalid score weights")
        if self.weights and (set(self.weights) != allowed or sum(self.weights.values()) != 100):
            raise ValueError("Supply all weights adding to 100")
        if any(not role.strip() or len(role) > 200 for role in self.target_roles):
            raise ValueError("Invalid role preference")
        return self


@router.get("/settings", response_model=PreferencesData)
def settings(session: DB):
    return session.get(Preferences, 1) or PreferencesData()


@router.put("/settings", response_model=PreferencesData)
def save_settings(data: PreferencesData, session: DB, request: Request):
    if data.backup_dir:
        destination = Path(data.backup_dir).expanduser().resolve()
        if destination.is_relative_to(request.app.state.settings.storage_dir.resolve()):
            raise HTTPException(422, "Choose a backup folder outside storage")
    item = session.get(Preferences, 1) or Preferences(id=1)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    session.add(item)
    existing = session.get(Schedule, "daily_backup")
    if data.backup_dir and not existing:
        session.add(Schedule(name="daily_backup", kind="backup", payload={}, interval_seconds=86400, next_due=now()))
    elif not data.backup_dir and existing:
        session.delete(existing)
    session.commit()
    session.refresh(item)
    return item


@router.post("/tasks/backup", response_model=TaskOut, status_code=202)
def request_backup(session: DB):
    return enqueue(session, "backup", {})


class SheetData(StrictModel):
    spreadsheet_id: str = Field(pattern=r"^[A-Za-z0-9_-]{10,150}$")
    tab: str = Field(min_length=1, max_length=100)
    header_row: int = Field(default=1, ge=1, le=100)
    mapping: dict[str, str] = Field(default_factory=lambda: DEFAULT_MAPPING.copy())
    is_test_copy: Literal[True]
    sync_every_minutes: int = Field(default=0, ge=0, le=1440)

    @model_validator(mode="after")
    def protect_tracker(self):
        if self.spreadsheet_id == LIVE_SHEET_ID:
            raise ValueError("The live tracker is blocked")
        fields = {"url", "company", "title", "location", "deadline", "status", "sponsorship", "notes"}
        if not {"url", "company"} <= self.mapping.keys() or not self.mapping.keys() <= fields:
            raise ValueError("Invalid header mapping")
        if len(set(self.mapping.values())) != len(self.mapping) or any(not h.strip() for h in self.mapping.values()):
            raise ValueError("Mapped headers must be nonempty and unique")
        protected = {"deadline alert", "days left", self.mapping.get("notes", "Notes").casefold(), "notes"}
        if any(header.casefold() in protected for field, header in self.mapping.items() if field != "notes"):
            raise ValueError("Notes and formula headers cannot be used for managed fields")
        return self


@router.get("/sheets/config")
def sheet_config(session: DB):
    config = session.get(SheetConfig, 1)
    schedule = session.get(Schedule, "sheet_sync")
    last = session.scalar(select(Task).where(Task.kind.in_(["sheets_sync", "sheets_import"]), Task.status == "SUCCEEDED").order_by(Task.finished_at.desc()))
    missing = []
    try:
        client_settings()
    except NeedsInput:
        missing.append("GOOGLE_OAUTH_CLIENT_FILE")
    if not os.environ.get("OAUTH_ENCRYPTION_KEY"):
        missing.append("OAUTH_ENCRYPTION_KEY")
    return {"mode": "copy_status_write" if config and write_enabled(config.spreadsheet_id) else "read_only", "last_sync": last.finished_at.isoformat() if last else None, "config": {"spreadsheet_id": config.spreadsheet_id, "tab": config.tab, "header_row": config.header_row, "mapping": config.mapping, "is_test_copy": True, "sync_every_minutes": schedule.interval_seconds // 60 if schedule else 0} if config else None,
            "connected": session.get(OAuthCredential, "google") is not None,
            "missing": missing}


@router.put("/sheets/config")
def save_sheet(data: SheetData, session: DB):
    config = session.get(SheetConfig, 1) or SheetConfig(id=1)
    for key in ("spreadsheet_id", "tab", "header_row", "mapping"):
        setattr(config, key, getattr(data, key))
    session.add(config)
    schedule = session.get(Schedule, "sheet_sync")
    if data.sync_every_minutes:
        schedule = schedule or Schedule(name="sheet_sync", next_due=now(), payload={})
        schedule.kind = "sheets_import"
        schedule.interval_seconds = max(5, data.sync_every_minutes) * 60
        session.add(schedule)
    elif schedule:
        session.delete(schedule)
    session.commit()
    return {"saved": True}


@router.get("/sheets/rows")
def sheet_rows(session: DB):
    config = session.get(SheetConfig, 1)
    if not config:
        return []
    rows = session.scalars(select(SheetLink).where(SheetLink.spreadsheet_id == config.spreadsheet_id, SheetLink.tab == config.tab).order_by(SheetLink.row_number)).all()
    return [{"row_number": row.row_number, "job_id": row.job_id, "values": row.raw_values, "warning": row.warning} for row in rows]


@router.post("/sheets/oauth/start")
def start_oauth(session: DB):
    try:
        return {"url": start(session)}
    except NeedsInput as error:
        raise HTTPException(409, str(error)) from None


@public_router.get("/oauth/google/callback", response_class=HTMLResponse)
def oauth_callback(request: Request, session: DB):
    try:
        state, code = request.query_params.get("state", ""), request.query_params.get("code", "")
        if not state or not code or len(state) > 300 or len(code) > 4000:
            raise NeedsInput("Google connection was not completed. Start it again from the local app.")
        finish(session, state, code)
        return HTMLResponse("<p>Google connected. Close this tab and return to the local tracker.</p>", headers={"Content-Security-Policy": "default-src 'none'", "Referrer-Policy": "no-referrer"})
    except NeedsInput:
        return HTMLResponse("<p>Google connection could not be completed. Return to the local tracker and check configuration.</p>", status_code=400, headers={"Content-Security-Policy": "default-src 'none'", "Referrer-Policy": "no-referrer"})


@router.post("/tasks/sheets/{operation}", response_model=TaskOut, status_code=202)
def sheet_task(operation: Literal["import", "sync"], session: DB):
    if operation == "sync":
        config = session.get(SheetConfig, 1)
        if not config or not write_enabled(config.spreadsheet_id):
            raise HTTPException(403, "Sheet write-back is disabled for this copy.")
    return enqueue(session, "sheets_" + operation, {})
