"""add_sessions_and_password_resets_tables

Revision ID: 3d74c238d79f
Revises: 47a04956d444
Create Date: 2026-03-14 10:19:38.462270

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from core_inventory.models.types import GUID


# revision identifiers, used by Alembic.
revision: str = '3d74c238d79f'
down_revision: Union[str, None] = '47a04956d444'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sessions table
    op.create_table('sessions',
    sa.Column('id', GUID(), nullable=False),
    sa.Column('user_id', GUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    
    # Create password_resets table
    op.create_table('password_resets',
    sa.Column('id', GUID(), nullable=False),
    sa.Column('user_id', GUID(), nullable=False),
    sa.Column('otp', sa.String(length=6), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_user_id'), 'password_resets', ['user_id'], unique=False)
    op.create_index(op.f('ix_password_resets_otp'), 'password_resets', ['otp'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_password_resets_otp'), table_name='password_resets')
    op.drop_index(op.f('ix_password_resets_user_id'), table_name='password_resets')
    op.drop_table('password_resets')
    op.drop_index(op.f('ix_sessions_user_id'), table_name='sessions')
    op.drop_table('sessions')
