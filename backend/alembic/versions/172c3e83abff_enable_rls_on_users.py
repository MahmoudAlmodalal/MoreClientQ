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
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_users_tenant_email'
            ) THEN
                ALTER TABLE users DROP CONSTRAINT uq_users_tenant_email;
            END IF;

            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_users_email'
            ) THEN
                ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
            END IF;
        END $$;
        """
    )
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_policies
                WHERE schemaname = current_schema()
                  AND tablename = 'users'
                  AND policyname = 'tenant_isolation'
            ) THEN
                CREATE POLICY tenant_isolation ON users
                USING (
                    current_setting('app.bypass_rls', true) = 'on'
                    OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID
                )
                WITH CHECK (
                    current_setting('app.bypass_rls', true) = 'on'
                    OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID
                );
            ELSE
                DROP POLICY tenant_isolation ON users;
                CREATE POLICY tenant_isolation ON users
                USING (
                    current_setting('app.bypass_rls', true) = 'on'
                    OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID
                )
                WITH CHECK (
                    current_setting('app.bypass_rls', true) = 'on'
                    OR tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID
                );
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON users;")
    op.execute("ALTER TABLE users NO FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY;")
