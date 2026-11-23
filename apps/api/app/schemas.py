from datetime import date, datetime, timezone
from typing import Annotated, Literal
import re

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, field_validator
from app.services.urls import canonical_url

Nonempty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
Status = Literal["DISCOVERED", "SHORTLISTED", "SKIPPED", "EXPIRED", "WITHDRAWN"]


def as_utc(value: datetime) -> datetime:
    # SQLite drops timezone metadata; stored timestamps are always created in UTC.
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


UtcTimestamp = Annotated[datetime, AfterValidator(as_utc)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, from_attributes=True)


class ProfileData(StrictModel):
    display_name: str = Field(default="", max_length=200)
    email: str = Field(default="", max_length=320)
    target_locations: str = Field(default="", max_length=500)
    graduation_year: int | None = Field(default=None, ge=1900, le=2200)


class FactData(StrictModel):
    category: Literal["education", "experience", "project", "skill"]
    content: Nonempty = Field(max_length=10000)
    source: Nonempty = Field(max_length=500)
    verified: bool = False


class FactOut(FactData):
    id: str
    created_at: UtcTimestamp


class JobData(StrictModel):
    url: Nonempty = Field(max_length=2048)
    company: Nonempty = Field(max_length=200)
    title: Nonempty = Field(max_length=300)
    location: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=100000)
    deadline: date | None = None
    notes: str = Field(default="", max_length=10000)
    eligibility_requirements: str = Field(default="", max_length=20000)
    start_date: date | None = None

    @field_validator("url")
    @classmethod
    def normalize_url(cls, value):
        normalized = canonical_url(value)
        if len(normalized) > 2048:
            raise ValueError("URL is too long")
        return normalized


class JobOut(JobData):
    id: str
    sponsorship_snapshot: str
    sponsorship: Literal["UNVERIFIED", "CONFIRMED_YES", "CONFIRMED_NO"]
    licensed_sponsor: bool | None
    status: Status
    created_at: UtcTimestamp
    tracker_status: str | None


class StatusChange(StrictModel):
    status: Status
    expected_status: Status


class EventOut(StrictModel):
    id: str
    from_status: str | None
    to_status: str
    created_at: UtcTimestamp


class RequirementTerm(StrictModel):
    value: Nonempty = Field(max_length=200, description='An exact contiguous substring of its own quote, without rephrasing or inferred labels.')
    quote: Nonempty = Field(max_length=2000, description='A short exact contiguous source substring containing the value, with original words and punctuation.')


class RequirementGroundingError(ValueError):
    def __init__(self, reason, field):
        self.field = field
        super().__init__(reason)


class RequirementsData(StrictModel):
    skills: list[RequirementTerm] = Field(default_factory=list, max_length=50, description='Named technology tools or platforms explicitly used or required for this role. Exclude general abilities, sales activities and company/product background. Empty when none are stated.')
    education: list[RequirementTerm] = Field(default_factory=list, max_length=20)
    experience: list[RequirementTerm] = Field(default_factory=list, max_length=20)

    def grounded(self, text):
        source = ' '.join(text.split()).casefold()
        for category, terms in (('skills', self.skills), ('education', self.education), ('experience', self.experience)):
            seen = set()
            for index, term in enumerate(terms):
                value, quote = ' '.join(term.value.split()).casefold(), ' '.join(term.quote.split()).casefold()
                if quote not in source:
                    raise RequirementGroundingError('requirement_quote_not_in_source', f'{category}.{index}.quote:quote_not_in_source')
                if not re.search(r"(?<![\w+#])" + re.escape(value) + r"(?![\w+#])", quote):
                    raise RequirementGroundingError('requirement_term_not_in_quote', f'{category}.{index}.value:term_not_in_quote')
                if value in seen:
                    raise RequirementGroundingError('requirement_duplicate_term', f'{category}.{index}.value:duplicate_term')
                seen.add(value)
        return self
