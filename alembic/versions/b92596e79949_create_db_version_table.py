"""create db_version table

Revision ID: b92596e79949
Revises: 
Create Date: 2018-02-09 16:58:50.931088

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import func


# revision identifiers, used by Alembic.
revision = 'b92596e79949'
down_revision = None
branch_labels = None
depends_on = None

meta = sa.MetaData()

system_settings = sa.Table(
    'system_settings', meta,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('name', sa.String, nullable=False),
    sa.Column('value', sa.String, nullable=False),
    sa.Column('update_date', sa.DateTime, server_default=func.now()),
)

def upgrade():
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('value', sa.String, nullable=False),
        sa.Column('update_date', sa.DateTime, server_default=func.now()),
    )
    
    op.bulk_insert(system_settings,
        [{'name': 'db_version', 'value': revision}])
    

def downgrade():
    op.drop_table('system_settings')
