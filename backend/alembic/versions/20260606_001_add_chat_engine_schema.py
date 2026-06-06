"""add_chat_engine_schema

Revision ID: 20260606_001
Revises: 0f486d76726d
Create Date: 2026-06-06 13:39:36.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260606_001'
down_revision: Union[str, None] = '0f486d76726d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add title VARCHAR(255) NULL column to conversations
    op.add_column('conversations', sa.Column('title', sa.String(length=255), nullable=True))
    
    # Update existing status values to 'bot' if they aren't 'bot', 'handoff', or 'closed'
    op.execute("UPDATE conversations SET status = 'bot' WHERE status NOT IN ('bot', 'handoff', 'closed')")
    
    # 2. Alter status column: change default to 'bot', ensure it's not nullable
    op.alter_column('conversations', 'status',
               existing_type=sa.String(length=50),
               server_default='bot',
               existing_nullable=False)
               
    # 3. Add CHECK constraint (status IN ('bot', 'handoff', 'closed'))
    op.create_check_constraint(
        'check_conversations_status',
        'conversations',
        sa.text("status IN ('bot', 'handoff', 'closed')")
    )
    
    # 4. Add index idx_conversations_status on (tenant_id, status)
    op.create_index('idx_conversations_status', 'conversations', ['tenant_id', 'status'], unique=False)
    
    # 5. Enable RLS on conversations and messages (just to be safe, though already enabled)
    op.execute("ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE conversations FORCE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE messages ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE messages FORCE ROW LEVEL SECURITY;")

    # 5a. Align message validation with the chat data model
    op.create_check_constraint(
        'check_messages_role',
        'messages',
        sa.text("role IN ('user', 'assistant', 'system')")
    )
    op.create_check_constraint(
        'check_messages_tokens_used_nonnegative',
        'messages',
        sa.text("COALESCE(tokens_used, 0) >= 0")
    )
    
    # 6. Create/Update FOR ALL RLS policies on conversations and messages using tenant_id
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON conversations;")
    op.execute(
        "CREATE POLICY tenant_isolation ON conversations "
        "FOR ALL "
        "USING ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ") "
        "WITH CHECK ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ");"
    )
    
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON messages;")
    op.execute(
        "CREATE POLICY tenant_isolation ON messages "
        "FOR ALL "
        "USING ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ") "
        "WITH CHECK ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ");"
    )


def downgrade() -> None:
    # Drop policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON messages;")
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON conversations;")

    op.drop_constraint('check_messages_tokens_used_nonnegative', 'messages', type_='check')
    op.drop_constraint('check_messages_role', 'messages', type_='check')
    
    # Recreate original tenant isolation policies
    op.execute(
        "CREATE POLICY tenant_isolation ON conversations "
        "USING ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ") "
        "WITH CHECK ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ");"
    )
    
    op.execute(
        "CREATE POLICY tenant_isolation ON messages "
        "USING ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ") "
        "WITH CHECK ("
        "current_setting('app.bypass_rls', true) = 'on' OR "
        "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::UUID"
        ");"
    )
    
    # Drop index
    op.drop_index('idx_conversations_status', table_name='conversations')
    
    # Drop constraint
    op.drop_constraint('check_conversations_status', 'conversations', type_='check')
    
    # Revert status default
    op.alter_column('conversations', 'status',
               existing_type=sa.String(length=50),
               server_default='active',
               existing_nullable=False)
               
    # Drop column title
    op.drop_column('conversations', 'title')
