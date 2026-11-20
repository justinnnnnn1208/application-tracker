"""Dated, owner-imported register cache, separate from role sponsorship."""
from alembic import op
import sqlalchemy as sa

revision = 'c96ef370a165'
down_revision = 'b85de269f054'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('sponsor_register',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_url', sa.String(2048), nullable=False),
        sa.Column('as_of', sa.Date(), nullable=False),
        sa.Column('sha256', sa.String(64), nullable=False),
        sa.Column('rows_read', sa.Integer(), nullable=False),
        sa.Column('organisations', sa.Integer(), nullable=False),
        sa.Column('imported_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('id = 1', name='singleton_sponsor_register'))
    op.create_table('sponsor_organisations',
        sa.Column('key', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('normalized', sa.String(1000), nullable=False),
        sa.Column('routes', sa.JSON(), nullable=False),
        sa.Column('towns', sa.JSON(), nullable=False))


def downgrade():
    op.drop_table('sponsor_organisations')
    op.drop_table('sponsor_register')
