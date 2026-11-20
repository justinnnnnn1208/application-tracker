"""Cache source-bound local model extraction without applicant inputs."""
from alembic import op
import sqlalchemy as sa

revision = 'b85de269f054'
down_revision = 'a74cd158ef43'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('job_requirements',
        sa.Column('job_id', sa.String(36), sa.ForeignKey('jobs.id'), primary_key=True),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('inputs_hash', sa.String(64), nullable=False),
        sa.Column('model', sa.String(200), nullable=False),
        sa.Column('source_chars', sa.Integer(), nullable=False),
        sa.Column('truncated', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))


def downgrade():
    op.drop_table('job_requirements')
