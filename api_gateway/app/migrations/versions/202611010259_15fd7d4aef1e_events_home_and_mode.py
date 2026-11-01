"""events home and mode

Revision ID: 15fd7d4aef1e
Revises: ab554225eb9d
Create Date: 2026-11-01 02:59:08.096806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15fd7d4aef1e'
down_revision: Union[str, None] = 'ab554225eb9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('home_id', sa.Integer(), nullable=True))
        batch_op.alter_column('device_id', existing_type=sa.INTEGER(), nullable=True)
        batch_op.create_index(batch_op.f('ix_events_home_id'), ['home_id'], unique=False)
        batch_op.create_foreign_key('fk_events_home_id_homes', 'homes', ['home_id'], ['id'], ondelete='CASCADE')
    # старые записи: дом — по устройству
    op.execute("UPDATE events SET home_id = (SELECT devices.home_id FROM devices WHERE devices.id = events.device_id) "
               "WHERE home_id IS NULL")


def downgrade() -> None:
    op.execute("DELETE FROM events WHERE device_id IS NULL")
    with op.batch_alter_table('events', schema=None) as batch_op:
        batch_op.drop_constraint('fk_events_home_id_homes', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_events_home_id'))
        batch_op.alter_column('device_id', existing_type=sa.INTEGER(), nullable=False)
        batch_op.drop_column('home_id')
