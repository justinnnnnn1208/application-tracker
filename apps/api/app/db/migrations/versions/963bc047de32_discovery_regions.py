"""Explicit employer/region for public API discovery without guessing names."""
from alembic import op
import sqlalchemy as sa

revision = '963bc047de32'
down_revision = '852ab936cd21'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('discovery_sources', sa.Column('employer', sa.String(200), server_default='', nullable=False))
    op.add_column('discovery_sources', sa.Column('region', sa.String(10), server_default='global', nullable=False))


def downgrade():
    with op.batch_alter_table('discovery_sources') as batch:
        batch.drop_column('region')
        batch.drop_column('employer')
