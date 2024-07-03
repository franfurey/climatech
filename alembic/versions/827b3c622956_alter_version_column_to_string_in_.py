"""Alter version column to string in wildfire_data table

Revision ID: 827b3c622956
Revises: 5cecaf787c43
Create Date: 2024-07-02 20:58:36.579870

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '827b3c622956'
down_revision = '5cecaf787c43'
branch_labels = None
depends_on = None

def upgrade():
    # Changes the column 'version' from Float to String
    op.alter_column('wildfire_data', 'version',
                    existing_type=sa.Float(),
                    type_=sa.String(),
                    existing_nullable=True)

def downgrade():
    # Reverts the column 'version' from String to Float
    op.alter_column('wildfire_data', 'version',
                    existing_type=sa.String(),
                    type_=sa.Float(),
                    existing_nullable=True)
