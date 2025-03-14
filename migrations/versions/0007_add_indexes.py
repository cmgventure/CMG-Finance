"""add_indexes

Revision ID: 0007
Revises: 0006
Create Date: 2025-03-03 02:22:00.908914

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index("companies__cik", "companies", ["cik"], unique=False)
    op.create_index("ix_fmp_categories_label_lower", "fmp_categories", [sa.text("lower(label)")], unique=False)
    op.create_index(op.f("ix_fmp_statements_category_id"), "fmp_statements", ["category_id"], unique=False)
    op.create_index(op.f("ix_fmp_statements_cik"), "fmp_statements", ["cik"], unique=False)
    op.create_index(op.f("ix_fmp_statements_period"), "fmp_statements", ["period"], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_fmp_statements_period"), table_name="fmp_statements")
    op.drop_index(op.f("ix_fmp_statements_cik"), table_name="fmp_statements")
    op.drop_index(op.f("ix_fmp_statements_category_id"), table_name="fmp_statements")
    op.drop_index("ix_fmp_categories_label_lower", table_name="fmp_categories")
    op.drop_index("companies__cik", table_name="companies")
    # ### end Alembic commands ###
