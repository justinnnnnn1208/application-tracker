"""Exact organisation-name signal against a dated owner-confirmed CSV snapshot."""
import csv
import hashlib
import json
import re
import unicodedata
from datetime import date, datetime
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator, model_validator
from sqlalchemy import delete, insert

from app.db.models import SponsorOrganisation, SponsorRegister, now
from app.schemas import Nonempty, StrictModel, as_utc
from app.services.errors import NeedsInput
from app.services.urls import canonical_url

MAX_BYTES = 50_000_000
MAX_ROWS = 1_000_000


class RegisterImport(StrictModel):
    source_url: Nonempty = Field(max_length=2048)
    as_of: date
    organisation_header: Nonempty = Field(max_length=200)
    route_header: Nonempty = Field(max_length=200)
    town_header: str = Field(default='', max_length=200)
    confirmed: bool

    @field_validator('source_url')
    @classmethod
    def official_csv_reference(cls, value):
        value = canonical_url(value)
        parts = urlsplit(value)
        if parts.scheme != 'https' or parts.hostname != 'assets.publishing.service.gov.uk' or parts.port is not None or parts.query or parts.fragment or not parts.path.startswith('/media/') or not parts.path.lower().endswith('.csv'):
            raise ValueError('Use the official register CSV asset URL')
        return value

    @model_validator(mode='after')
    def validate_metadata(self):
        if not self.confirmed or self.as_of > datetime.now(ZoneInfo('Europe/London')).date() or self.as_of < date(2000, 1, 1):
            raise ValueError('Confirm the register provenance and publication date')
        fields = [self.organisation_header, self.route_header] + ([self.town_header] if self.town_header else [])
        if len(set(fields)) != len(fields):
            raise ValueError('Map distinct organisation/route/town columns')
        return self


def normal_name(value):
    return ' '.join(unicodedata.normalize('NFC', value).split()).casefold()


def name_key(value):
    return hashlib.sha256(normal_name(value).encode()).hexdigest()


def parse(file, config):
    organisations, rows_read = {}, 0
    try:
        reader = csv.DictReader(file, strict=True)
        headers = reader.fieldnames or []
        required = [config.organisation_header, config.route_header] + ([config.town_header] if config.town_header else [])
        if len(headers) != len(set(headers)) or not set(required) <= set(headers):
            raise ValueError('Invalid or unmapped headers')
        for row in reader:
            rows_read += 1
            if rows_read > MAX_ROWS or None in row:
                raise ValueError('Oversized or malformed row')
            name, route = (row.get(config.organisation_header) or '').strip(), (row.get(config.route_header) or '').strip()
            town = (row.get(config.town_header) or '').strip() if config.town_header else ''
            normalized = normal_name(name)
            if not name or not route or len(name) > 500 or len(normalized) > 1000 or len(route) > 200 or len(town) > 300:
                raise ValueError('Invalid organisation row')
            key = name_key(name)
            record = organisations.setdefault(key, {'key': key, 'name': name, 'normalized': normalized, 'routes': set(), 'towns': set()})
            if record['normalized'] != normalized:
                raise ValueError('Conflicting organisation identity')
            record['routes'].add(route)
            if town:
                record['towns'].add(town)
        if not organisations:
            raise ValueError('Empty register')
    except (ValueError, csv.Error, UnicodeError):
        raise NeedsInput('Register CSV is empty, malformed, too large or does not match the selected columns. No register data was replaced.') from None
    return [{**row, 'routes': sorted(row['routes']), 'towns': sorted(row['towns'])} for row in organisations.values()], rows_read


def import_register(session, settings, payload):
    if not re.fullmatch(r'[a-f0-9-]{36}', payload.get('file_id', '')):
        raise NeedsInput('Invalid register upload identity.')
    config = RegisterImport.model_validate(payload['config'])
    path = settings.storage_dir / 'registers' / (payload['file_id'] + '.csv')
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise NeedsInput('Register upload is missing or too large. No register data was replaced.')
    with path.open(encoding='utf-8-sig', newline='') as file:
        entries, rows_read = parse(file, config)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    # Parse completely before replacing only the public cache. Owner jobs/history stay untouched.
    session.execute(delete(SponsorOrganisation))
    for start in range(0, len(entries), 1000):
        session.execute(insert(SponsorOrganisation), entries[start:start + 1000])
    row = session.get(SponsorRegister, 1) or SponsorRegister(id=1)
    row.source_url, row.as_of, row.sha256 = config.source_url, config.as_of, digest
    row.rows_read, row.organisations, row.imported_at = rows_read, len(entries), now()
    session.add(row)
    # Keep uploaded snapshots for backup/provenance; do not delete past public captures.
    path.with_suffix('.json').write_text(json.dumps({**config.model_dump(mode='json'), 'sha256': digest, 'rows_read': rows_read, 'organisations': len(entries)}, indent=2))
    path.with_suffix('.json').chmod(0o600)
    session.commit()
    return {'rows_read': rows_read, 'organisations': len(entries), 'sha256': digest}


def metadata(session):
    row = session.get(SponsorRegister, 1)
    return None if not row else {'source_url': row.source_url, 'as_of': row.as_of, 'sha256': row.sha256,
                                'rows_read': row.rows_read, 'organisations': row.organisations, 'imported_at': as_utc(row.imported_at),
                                'verification': 'owner_confirmed_upload'}


def match(session, company):
    if not session.get(SponsorRegister, 1):
        return None, None
    row = session.get(SponsorOrganisation, name_key(company))
    if row and row.normalized == normal_name(company):
        return True, {'name': row.name, 'routes': row.routes, 'towns': row.towns}
    return False, None
