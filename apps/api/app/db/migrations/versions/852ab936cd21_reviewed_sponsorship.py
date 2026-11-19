"""Bind manually reviewed evidence to the saved vacancy content."""
from alembic import op
import sqlalchemy as sa

revision = '852ab936cd21'
down_revision = '7419a825bc10'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('job_eligibility', sa.Column('source_hash', sa.String(64), nullable=True))
    op.add_column('job_eligibility', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))


def downgrade():
    with op.batch_alter_table('job_eligibility') as batch:
        batch.drop_column('reviewed_at')
        batch.drop_column('source_hash')
