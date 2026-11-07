from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, JSON, UniqueConstraint, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profile"
    __table_args__ = (CheckConstraint("id = 1", name="singleton_profile"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    display_name: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(320), default="")
    target_locations: Mapped[str] = mapped_column(String(500), default="")
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Fact(Base):
    __tablename__ = "facts"
    __table_args__ = (CheckConstraint("category IN ('education', 'experience', 'project', 'skill')", name="fact_category"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    category: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(500))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (CheckConstraint("sponsorship = 'UNVERIFIED'", name="foundation_sponsorship"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    url: Mapped[str] = mapped_column(String(2048), unique=True)
    company: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(300))
    location: Mapped[str] = mapped_column(String(300), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    eligibility_requirements: Mapped[str] = mapped_column(Text, default="", server_default="")
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tracker_status: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sponsorship: Mapped[str] = mapped_column(String(30), default="UNVERIFIED")
    licensed_sponsor: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (CheckConstraint("status IN ('DISCOVERED', 'SHORTLISTED', 'SKIPPED', 'EXPIRED', 'WITHDRAWN')", name="foundation_status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), unique=True)
    status: Mapped[str] = mapped_column(String(40), default="DISCOVERED")


class ApplicationEvent(Base):
    __tablename__ = "application_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"), index=True)
    from_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (CheckConstraint("status IN ('QUEUED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'NEEDS_INPUT')", name="task_status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="QUEUED", index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    parent_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id"), nullable=True)
    format: Mapped[str] = mapped_column(String(10))
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class FactCandidate(Base):
    __tablename__ = "fact_candidates"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(30), nullable=True)
    fact_id: Mapped[str | None] = mapped_column(ForeignKey("facts.id", ondelete="SET NULL"), nullable=True)
    decision: Mapped[str] = mapped_column(String(20), default="PENDING")


class SheetConfig(Base):
    __tablename__ = "sheet_config"
    __table_args__ = (CheckConstraint("id = 1", name="singleton_sheet_config"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    spreadsheet_id: Mapped[str] = mapped_column(String(150))
    tab: Mapped[str] = mapped_column(String(100))
    header_row: Mapped[int] = mapped_column(Integer, default=1)
    mapping: Mapped[dict] = mapped_column(JSON)


class SheetLink(Base):
    __tablename__ = "sheet_links"
    __table_args__ = (UniqueConstraint("spreadsheet_id", "tab", "row_number", name="unique_sheet_row"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    spreadsheet_id: Mapped[str] = mapped_column(String(150))
    tab: Mapped[str] = mapped_column(String(100))
    row_number: Mapped[int] = mapped_column(Integer)
    job_id: Mapped[str | None] = mapped_column(ForeignKey("jobs.id"), nullable=True)
    row_hash: Mapped[str] = mapped_column(String(64))
    raw_values: Mapped[list] = mapped_column(JSON)
    raw_formulas: Mapped[list] = mapped_column(JSON)
    last_db_values: Mapped[dict] = mapped_column(JSON, default=dict)
    warning: Mapped[str | None] = mapped_column(String(300), nullable=True)


class OAuthCredential(Base):
    __tablename__ = "oauth_credentials"
    id: Mapped[str] = mapped_column(String(30), primary_key=True)
    ciphertext: Mapped[str] = mapped_column(Text)


class OAuthState(Base):
    __tablename__ = "oauth_states"
    digest: Mapped[str] = mapped_column(String(64), primary_key=True)
    encrypted_verifier: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Preferences(Base):
    __tablename__ = "preferences"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    backup_dir: Mapped[str] = mapped_column(String(2048), default="")
    target_roles: Mapped[list] = mapped_column(JSON, default=list)
    weights: Mapped[dict] = mapped_column(JSON, default=dict)


class Schedule(Base):
    __tablename__ = "schedules"
    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    kind: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    interval_seconds: Mapped[int] = mapped_column(Integer)
    next_due: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class JobEligibility(Base):
    __tablename__ = "job_eligibility"
    __table_args__ = (CheckConstraint("status = 'UNVERIFIED' OR (evidence_quote IS NOT NULL AND source_url IS NOT NULL)", name="eligibility_evidence"),)
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), default="UNVERIFIED")
    evidence_quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    licensed_sponsor: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class MatchResult(Base):
    __tablename__ = "match_results"
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"), primary_key=True)
    score: Mapped[int] = mapped_column(Integer)
    breakdown: Mapped[list] = mapped_column(JSON)
    inputs_hash: Mapped[str] = mapped_column(String(64))
    feedback: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class DiscoverySource(Base):
    __tablename__ = "discovery_sources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(30))
    board: Mapped[str] = mapped_column(String(150))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class SensitiveDeclaration(Base):
    __tablename__ = "sensitive_declarations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    category: Mapped[str] = mapped_column(String(40))
    question: Mapped[str] = mapped_column(String(500))
    value: Mapped[str] = mapped_column(Text)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)


@event.listens_for(ApplicationEvent, "before_update")
@event.listens_for(ApplicationEvent, "before_delete")
def immutable_event(*_):
    raise ValueError("Application events are append-only")
