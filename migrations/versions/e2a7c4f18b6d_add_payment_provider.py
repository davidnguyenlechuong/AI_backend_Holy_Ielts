"""add payment_provider to orders

Revision ID: e2a7c4f18b6d
Revises: c1f4a7e2b9d3
Create Date: 2026-08-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e2a7c4f18b6d'
down_revision: Union[str, Sequence[str], None] = 'c1f4a7e2b9d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'orders',
        sa.Column('payment_provider', sa.String(length=20), nullable=False, server_default='SEPAY'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('orders', 'payment_provider')
