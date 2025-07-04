"""add email password to amazfit credentials

Revision ID: add_email_password_to_amazfit_credentials
Revises: c1812858690c
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_email_password_to_amazfit_credentials'
down_revision = 'c1812858690c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email and password columns to amazfit_credentials table
    op.add_column('amazfit_credentials', sa.Column('email', sa.String(), nullable=True))
    op.add_column('amazfit_credentials', sa.Column('password', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove email and password columns from amazfit_credentials table
    op.drop_column('amazfit_credentials', 'password')
    op.drop_column('amazfit_credentials', 'email') 