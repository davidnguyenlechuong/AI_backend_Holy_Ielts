"""switch orders to pg_transaction_id

Revision ID: c1f4a7e2b9d3
Revises: 8a2b22bb492d
Create Date: 2026-08-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c1f4a7e2b9d3'
down_revision: Union[str, Sequence[str], None] = '8a2b22bb492d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('orders_sepay_transaction_id_key', 'orders', type_='unique')
    op.drop_column('orders', 'sepay_transaction_id')
    op.add_column('orders', sa.Column('pg_transaction_id', sa.String(length=100), nullable=True))
    op.create_unique_constraint('orders_pg_transaction_id_key', 'orders', ['pg_transaction_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('orders_pg_transaction_id_key', 'orders', type_='unique')
    op.drop_column('orders', 'pg_transaction_id')
    op.add_column('orders', sa.Column('sepay_transaction_id', sa.BigInteger(), nullable=True))
    op.create_unique_constraint('orders_sepay_transaction_id_key', 'orders', ['sepay_transaction_id'])
