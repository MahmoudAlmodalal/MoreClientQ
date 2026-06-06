"""Create invitations table and enable RLS

Revision ID: a1b2c3d4e5f6
Revises: 172c3e83abff
Create Date: 2026-06-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '172c3e83abff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('invitations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_invitations_token'), 'invitations', ['token'], unique=True)
    op.create_index(op.f('ix_invitations_tenant_id'), 'invitations', ['tenant_id'], unique=False)

    # Enable RLS on invitations table
    op.execute("ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE invitations FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY IF NOT EXISTS tenant_isolation ON invitations "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON invitations;")
    op.execute("ALTER TABLE invitations NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE invitations DISABLE ROW LEVEL SECURITY;")
    op.drop_index(op.f('ix_invitations_tenant_id'), table_name='invitations')
    op.drop_index(op.f('ix_invitations_token'), table_name='invitations')
    op.drop_table('invitations')
