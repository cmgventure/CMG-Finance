"""add user password hash

Revision ID: 0003
Revises: 0001
Create Date: 2024-11-04 18:48:15.918120

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)
    op.add_column('users', sa.Column('password_hash', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'password_hash')
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    # ### end Alembic commands ###
