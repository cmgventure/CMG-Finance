"""add uq constraint for categories

Revision ID: 0003
Revises: 0002
Create Date: 2024-11-05 18:18:27.865265

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint("uq_label_value_definition_type", "categories", ["label", "value_definition", "type"])


def downgrade() -> None:
    op.drop_constraint("uq_label_value_definition_type", "categories")
