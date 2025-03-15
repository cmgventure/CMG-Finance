"""add_v2_tables

Revision ID: 0009
Revises: 0008
Create Date: 2025-03-14 17:16:17.003198

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "companies_v2",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("cik", sa.String(), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sic", sa.String(), nullable=True),
        sa.Column("business_address", sa.String(), nullable=True),
        sa.Column("mailing_address", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("sector", sa.String(), nullable=True),
        sa.Column("industry", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True),
        sa.Column("market_cap", sa.Numeric(precision=38, scale=2), nullable=True),
        sa.Column("p/e", sa.Numeric(precision=38, scale=2), nullable=True),
        sa.Column("price", sa.Numeric(precision=38, scale=2), nullable=True),
        sa.Column("change", sa.Numeric(precision=38, scale=2), nullable=True),
        sa.Column("volume", sa.Numeric(precision=38, scale=2), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cik", "ticker", name="uq_cik_ticker"),
    )
    op.create_index("idx_cik_ticker", "companies_v2", ["cik", "ticker"], unique=False)
    op.create_index(op.f("ix_companies_v2_cik"), "companies_v2", ["cik"], unique=False)
    op.create_index(op.f("ix_companies_v2_ticker"), "companies_v2", ["ticker"], unique=False)
    op.create_table(
        "fmp_statements_v2",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("period", sa.String(), nullable=True),
        sa.Column("filing_date", sa.String(), nullable=False),
        sa.Column("report_date", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(precision=38, scale=4), nullable=False),
        sa.Column("company_id", sa.UUID(), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["fmp_categories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies_v2.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "period", "category_id", name="uq_company_id_period_category_id"),
    )
    op.create_index(
        "idx_company_id_period_category_id", "fmp_statements_v2", ["company_id", "period", "category_id"], unique=False
    )
    op.create_index(op.f("ix_fmp_statements_v2_category_id"), "fmp_statements_v2", ["category_id"], unique=False)
    op.create_index(op.f("ix_fmp_statements_v2_company_id"), "fmp_statements_v2", ["company_id"], unique=False)
    op.create_index(op.f("ix_fmp_statements_v2_period"), "fmp_statements_v2", ["period"], unique=False)
    op.alter_column("fmp_categories", "label", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("fmp_categories", "value_definition", existing_type=sa.VARCHAR(), nullable=False)
    op.drop_index("ix_fmp_categories_id", table_name="fmp_categories")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index("ix_fmp_categories_id", "fmp_categories", ["id"], unique=False)
    op.alter_column("fmp_categories", "value_definition", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("fmp_categories", "label", existing_type=sa.VARCHAR(), nullable=True)
    op.drop_index(op.f("ix_fmp_statements_v2_period"), table_name="fmp_statements_v2")
    op.drop_index(op.f("ix_fmp_statements_v2_company_id"), table_name="fmp_statements_v2")
    op.drop_index(op.f("ix_fmp_statements_v2_category_id"), table_name="fmp_statements_v2")
    op.drop_index("idx_company_id_period_category_id", table_name="fmp_statements_v2")
    op.drop_table("fmp_statements_v2")
    op.drop_index(op.f("ix_companies_v2_ticker"), table_name="companies_v2")
    op.drop_index(op.f("ix_companies_v2_cik"), table_name="companies_v2")
    op.drop_index("idx_cik_ticker", table_name="companies_v2")
    op.drop_table("companies_v2")
    # ### end Alembic commands ###
