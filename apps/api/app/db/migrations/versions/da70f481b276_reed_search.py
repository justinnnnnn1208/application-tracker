"""Public search configuration and cached Reed identity scope; no job/history merges."""
import re
from urllib.parse import urlsplit
from alembic import op
import sqlalchemy as sa

revision = 'da70f481b276'
down_revision = 'c96ef370a165'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('discovery_sources', sa.Column('search_query', sa.String(300), nullable=False, server_default=''))
    connection = op.get_bind()
    for row in list(connection.execute(sa.text('SELECT id,url,identity_key FROM job_sources'))):
        parts = urlsplit(row.url)
        match = re.fullmatch(r'/jobs/[^/]+/([0-9]{1,15})/?', parts.path)
        if not row.identity_key and parts.hostname in {'reed.co.uk', 'www.reed.co.uk'} and parts.port is None and match and int(match[1]) > 0:
            connection.execute(sa.text('UPDATE job_sources SET identity_key=:key WHERE id=:id'), {'key': f'reed:jobs:{int(match[1])}', 'id': row.id})


def downgrade():
    op.execute("UPDATE job_sources SET identity_key='' WHERE identity_key LIKE 'reed:jobs:%'")
    with op.batch_alter_table('discovery_sources') as batch:
        batch.drop_column('search_query')
