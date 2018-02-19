"""create user table

Revision ID: fdde231cde4f
Revises: b92596e79949
Create Date: 2018-02-09 20:48:40.589722

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdde231cde4f'
down_revision = 'b92596e79949'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('login', sa.String, nullable=False, unique=True),
        sa.Column('password', sa.String, nullable=False),
        sa.Column('first_name', sa.String, nullable=True),
        sa.Column('last_name', sa.String, nullable=True),
        sa.Column('email', sa.String, nullable=True)
    )

    op.create_table(
        'permission',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id', ondelete="CASCADE"), nullable=False),
        sa.Column('name', sa.String, nullable=False)
    )


def downgrade():
    op.drop_table('user')
    op.drop_table('pernission')
