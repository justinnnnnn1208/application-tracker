"""Scope cached provider IDs to global/EU instances without merging histories."""
from urllib.parse import urlsplit
from alembic import op
import sqlalchemy as sa

revision = 'a74cd158ef43'
down_revision = '963bc047de32'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    rows = list(connection.execute(sa.text('SELECT id,url,identity_key FROM job_sources')))
    for row in rows:
        host = urlsplit(row.url).hostname
        provider = {'jobs.eu.lever.co': 'lever', 'boards.eu.greenhouse.io': 'greenhouse', 'job-boards.eu.greenhouse.io': 'greenhouse'}.get(host)
        if provider and row.identity_key and row.identity_key.startswith(provider + ':'):
            key = provider + '-eu:' + row.identity_key[len(provider) + 1:]
            connection.execute(sa.text('UPDATE job_sources SET identity_key=:key WHERE id=:id'), {'key': key, 'id': row.id})


def downgrade():
    connection = op.get_bind()
    for row in list(connection.execute(sa.text('SELECT id,identity_key FROM job_sources'))):
        key = row.identity_key or ''
        for provider in ('lever', 'greenhouse'):
            if key.startswith(provider + '-eu:'):
                connection.execute(sa.text('UPDATE job_sources SET identity_key=:key WHERE id=:id'), {'key': provider + ':' + key[len(provider) + 4:], 'id': row.id})
