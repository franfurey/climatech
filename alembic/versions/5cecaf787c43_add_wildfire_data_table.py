"""Add wildfire_data table

Revision ID: 5cecaf787c43
Revises: 0c200b07e4b2
Create Date: 2024-07-02 20:02:21.658286

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2



# revision identifiers, used by Alembic.
revision: str = '5cecaf787c43'
down_revision: Union[str, None] = '0c200b07e4b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table('wildfire_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('brightness', sa.Float(), nullable=True),
        sa.Column('scan', sa.Float(), nullable=True),
        sa.Column('track', sa.Float(), nullable=True),
        sa.Column('acq_date', sa.DateTime(), nullable=True),
        sa.Column('acq_time', sa.String(), nullable=True),
        sa.Column('satellite', sa.String(), nullable=True),
        sa.Column('confidence', sa.String(), nullable=True),
        sa.Column('version', sa.Float(), nullable=True),
        sa.Column('bright_t31', sa.Float(), nullable=True),
        sa.Column('frp', sa.Float(), nullable=True),
        sa.Column('daynight', sa.String(), nullable=True),
        sa.Column('location', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # Comentamos la creación de índices
    # op.create_index('idx_wildfire_data_location', 'wildfire_data', ['location'], unique=False, postgresql_using='gist')
    # op.create_index(op.f('ix_wildfire_data_acq_date'), 'wildfire_data', ['acq_date'], unique=False)


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'harmonized_landsat_sentinel_data', type_='foreignkey')
    op.create_foreign_key('harmonized_landsat_sentinel_data_place_id_fkey', 'harmonized_landsat_sentinel_data', 'places', ['place_id'], ['id'])
    op.drop_index(op.f('ix_wildfire_data_acq_date'), table_name='wildfire_data')
    op.drop_index('idx_wildfire_data_location', table_name='wildfire_data', postgresql_using='gist')
    op.drop_table('wildfire_data')
    # ### end Alembic commands ###