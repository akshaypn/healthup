"""
Revision ID: 854a8449cb83
Revises: 1f69e06673a2
Create Date: 2025-07-04 00:25:08.292839

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '854a8449cb83'
down_revision = '1f69e06673a2'
branch_labels = None
depends_on = None

def upgrade():
    # Remove unused columns from amazfit_credentials table
    op.drop_column('amazfit_credentials', 'access_token')
    op.drop_column('amazfit_credentials', 'device_mac')
    op.drop_column('amazfit_credentials', 'auth_key')

def downgrade():
    # Add back the removed columns
    op.add_column('amazfit_credentials', sa.Column('access_token', sa.Text(), nullable=True))
    op.add_column('amazfit_credentials', sa.Column('device_mac', sa.String(), nullable=True))
    op.add_column('amazfit_credentials', sa.Column('auth_key', sa.String(), nullable=True)) 