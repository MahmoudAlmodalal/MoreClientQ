"""enable_rls_on_users

Revision ID: 172c3e83abff
Revises: 9a14eb0d81cc
Create Date: 2026-06-06 11:02:50.221427

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '172c3e83abff'
down_revision: Union[str, None] = '9a14eb0d81cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute(
        "CREATE POLICY IF NOT EXISTS tenant_isolation ON users "
        "USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID);"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON users;")
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
