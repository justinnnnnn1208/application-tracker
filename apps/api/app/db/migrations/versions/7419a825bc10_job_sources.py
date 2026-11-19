"""Preserve source URLs without merging existing jobs or application histories."""
from alembic import op
import sqlalchemy as sa

revision = '7419a825bc10'
down_revision = '5103adc629a6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('job_sources',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('jobs.id'), nullable=False),
        sa.Column('url', sa.String(2048), nullable=False, unique=True),
        sa.Column('identity_key', sa.String(300), nullable=True),
        sa.Column('method', sa.String(30), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_job_sources_job_id', 'job_sources', ['job_id'])
    op.create_index('ix_job_sources_identity_key', 'job_sources', ['identity_key'])
    op.execute("INSERT INTO job_sources (id, job_id, url, identity_key, method, created_at) SELECT id, id, url, NULL, 'primary', created_at FROM jobs")


def downgrade():
    op.drop_index('ix_job_sources_identity_key', table_name='job_sources')
    op.drop_index('ix_job_sources_job_id', table_name='job_sources')
    op.drop_table('job_sources')
