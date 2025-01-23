"""update categories columns

Revision ID: 0002
Revises: 0000
Create Date: 2024-10-30 13:32:19.696674

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = "0000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Ensure the uuid-ossp extension exists
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Add 'id' column to 'categories' table
    op.add_column(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text("gen_random_uuid()")),
    )

    # **First**, drop the foreign key constraint on 'financial_statements.tag'
    op.drop_constraint(
        "financial_statements_tag_fkey",  # Adjust the constraint name if different
        "financial_statements",
        type_="foreignkey",
    )

    # Now, drop old primary key constraint on 'categories'
    op.drop_constraint("categories_pkey", "categories", type_="primary")

    # Rename 'label' to 'description'
    op.alter_column("categories", "label", new_column_name="description")

    # Rename 'category' to 'label'
    op.alter_column("categories", "category", new_column_name="label")

    # Rename 'tag' to 'value_definition'
    op.alter_column("categories", "tag", new_column_name="value_definition")

    # Create new primary key on 'categories' with 'id'
    op.create_primary_key("categories_pkey", "categories", ["id"])

    # Create ENUM type for 'type' column
    category_type_enum = postgresql.ENUM("api_tag", "custom_formula", "exact_value", name="categorydefinitiontype")
    category_type_enum.create(op.get_bind(), checkfirst=True)

    # Add 'priority' and 'type' columns to 'categories'
    op.add_column("categories", sa.Column("priority", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("categories", sa.Column("type", category_type_enum, nullable=True, server_default="api_tag"))

    # Add 'category_id' column to 'financial_statements' table
    op.add_column("financial_statements", sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True))

    # Update 'financial_statements.category_id' with corresponding 'categories.id'
    op.execute(
        """
            UPDATE financial_statements AS fs
            SET category_id = c.id
            FROM categories AS c
            WHERE fs.tag = c.value_definition
        """
    )

    # Drop 'tag' column from 'financial_statements'
    op.drop_column("financial_statements", "tag")

    # Alter 'category_id' to be not nullable
    op.alter_column("financial_statements", "category_id", existing_type=postgresql.UUID(), nullable=False)

    # Recreate primary key constraint including 'category_id'
    op.create_primary_key(
        "financial_statements_pkey",
        "financial_statements",
        ["accession_number", "period", "filing_date", "report_date", "cik", "category_id"],
    )

    # Add new foreign key constraint on 'category_id'
    op.create_foreign_key(
        "financial_statements_category_id_fkey", "financial_statements", "categories", ["category_id"], ["id"]
    )

    # Optionally, create the check constraint on 'categories'
    op.create_check_constraint("categories_priority_nz", "categories", "priority >= 1")


def downgrade() -> None:
    pass
