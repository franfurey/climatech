"""Add NDVI column

Revision ID: 0c200b07e4b2
Revises: cc4ed6cc1407
Create Date: 2024-06-25 18:59:10.382186

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c200b07e4b2'
down_revision: Union[str, None] = 'cc4ed6cc1407'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('harmonized_landsat_sentinel_data', sa.Column('ndvi', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('harmonized_landsat_sentinel_data', 'ndvi')
    # ### end Alembic commands ###
