"""Add food log analysis table

Revision ID: add_food_log_analysis
Revises: c1812858690c
Create Date: 2025-01-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_food_log_analysis'
down_revision = 'c1812858690c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create food_log_analyses table
    op.create_table('food_log_analyses',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('food_log_id', sa.BigInteger(), nullable=False),
        sa.Column('health_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('protein_adequacy', sa.String(), nullable=True),
        sa.Column('fiber_content', sa.String(), nullable=True),
        sa.Column('vitamin_balance', sa.String(), nullable=True),
        sa.Column('mineral_balance', sa.String(), nullable=True),
        sa.Column('recommendations', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('analysis_text', sa.Text(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['food_log_id'], ['food_logs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('food_log_analyses') 