"""Index official SmartRecruiters listing aliases without merging job histories."""
import re
from urllib.parse import urlsplit
from alembic import op
import sqlalchemy as sa

revision = 'eb81a592c387'
down_revision = 'da70f481b276'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    for row in list(connection.execute(sa.text('SELECT id,url,identity_key FROM job_sources'))):
        parts = urlsplit(row.url)
        match = re.fullmatch(r'/([A-Za-z0-9_-]{1,100})/([0-9]{1,30})(?:-[^/]+)?/?', parts.path)
        if not row.identity_key and parts.hostname == 'jobs.smartrecruiters.com' and parts.port is None and match and int(match[2]) > 0:
            connection.execute(sa.text('UPDATE job_sources SET identity_key=:key WHERE id=:id'), {'key': f'smartrecruiters:{match[1]}:{int(match[2])}', 'id': row.id})


def downgrade():
    op.execute("UPDATE job_sources SET identity_key='' WHERE identity_key LIKE 'smartrecruiters:%'")
