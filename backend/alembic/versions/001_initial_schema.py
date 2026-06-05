"""001_initial_schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-06-05 10:19:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Tenants Table
    op.create_table(
        'tenants',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('plan', sa.String(length=50), server_default='free', nullable=False),
        sa.Column('region', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Workspaces Table
    op.create_table(
        'workspaces',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('company_info', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('branding', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timezone', sa.String(length=100), server_default='UTC', nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )

    # 3. Assistants Table
    op.create_table(
        'assistants',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('avatar_url', sa.String(length=512), nullable=True),
        sa.Column('personality', sa.String(length=50), server_default='professional', nullable=False),
        sa.Column('language_mode', sa.String(length=20), server_default='bilingual', nullable=False),
        sa.Column('guardrails', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_assistants_tenant', 'assistants', ['tenant_id'], unique=False)

    # 4. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('email_verified', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # 5. Knowledge Sources Table
    op.create_table(
        'knowledge_sources',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='processing', nullable=False),
        sa.Column('file_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_knowledge_sources_tenant', 'knowledge_sources', ['tenant_id'], unique=False)

    # 6. Knowledge Versions Table
    op.create_table(
        'knowledge_versions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('version_number', sa.String(length=50), nullable=False),
        sa.Column('change_log', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_knowledge_versions_tenant', 'knowledge_versions', ['tenant_id'], unique=False)

    # 7. Human Agents Table
    op.create_table(
        'human_agents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('skills', postgresql.ARRAY(sa.String(length=50)), server_default='{}', nullable=False),
        sa.Column('availability_status', sa.String(length=50), server_default='offline', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agents_email', 'human_agents', ['email'], unique=True)
    op.create_index('idx_agents_tenant', 'human_agents', ['tenant_id'], unique=False)
    op.create_index('idx_agents_tenant_status', 'human_agents', ['tenant_id', 'availability_status'], unique=False)

    # 8. Conversations Table
    op.create_table(
        'conversations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('workspace_id', sa.UUID(), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('channel', sa.String(length=50), server_default='web', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='ai', nullable=False),
        sa.Column('intent', sa.String(length=100), nullable=True),
        sa.Column('sentiment_score', sa.Integer(), nullable=True),
        sa.Column('urgency', sa.String(length=20), server_default='low', nullable=False),
        sa.Column('assigned_agent_id', sa.UUID(), nullable=True),
        sa.Column('csat_triggered', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('csat_score', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_agent_id'], ['human_agents.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversations_tenant', 'conversations', ['tenant_id'], unique=False)
    op.create_index('idx_conversations_status', 'conversations', ['status'], unique=False)
    op.create_index('idx_conversations_tenant_status', 'conversations', ['tenant_id', 'status'], unique=False)
    op.create_index('idx_conversations_agent', 'conversations', ['assigned_agent_id'], unique=False)

    # 9. Messages Table
    op.create_table(
        'messages',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('sender_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_messages_conversation', 'messages', ['conversation_id'], unique=False)

    # 10. Leads Table
    op.create_table(
        'leads',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('channel', sa.String(length=50), nullable=True),
        sa.Column('estimated_value', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('pipeline_stage', sa.String(length=50), server_default='new', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_leads_tenant', 'leads', ['tenant_id'], unique=False)

    # 11. Subscriptions Table
    op.create_table(
        'subscriptions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('plan_type', sa.String(length=50), nullable=False),
        sa.Column('billing_cycle', sa.String(length=20), server_default='monthly', nullable=False),
        sa.Column('limits', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('current_usage', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id')
    )

    # 12. Audit Logs Table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=False),
        sa.Column('actor_role', sa.String(length=50), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=255), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # --- ROW LEVEL SECURITY (RLS) ---
    tenant_scoped_tables = [
        'workspaces', 'assistants', 'users', 'knowledge_sources', 'knowledge_versions',
        'human_agents', 'conversations', 'messages', 'leads', 'subscriptions', 'audit_logs'
    ]

    for table in tenant_scoped_tables:
        # Enable RLS
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;"))
        # Create Policy
        op.execute(sa.text(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL
            USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
        """))

    # --- IMMUTABILITY TRIGGER FOR AUDIT LOGS ---
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are immutable and cannot be updated or deleted.';
        END;
        $$ LANGUAGE plpgsql;
    """))

    op.execute(sa.text("""
        CREATE TRIGGER audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_modification();
    """))

def downgrade() -> None:
    # Remove trigger & function
    op.execute(sa.text("DROP TRIGGER IF EXISTS audit_logs_immutable ON audit_logs;"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS prevent_audit_log_modification();"))

    tenant_scoped_tables = [
        'workspaces', 'assistants', 'users', 'knowledge_sources', 'knowledge_versions',
        'human_agents', 'conversations', 'messages', 'leads', 'subscriptions', 'audit_logs'
    ]

    for table in tenant_scoped_tables:
        op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};"))
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;"))

    # Drop tables
    op.drop_table('audit_logs')
    op.drop_table('subscriptions')
    op.drop_index('idx_leads_tenant', table_name='leads')
    op.drop_table('leads')
    op.drop_index('idx_messages_conversation', table_name='messages')
    op.drop_table('messages')
    op.drop_index('idx_conversations_agent', table_name='conversations')
    op.drop_index('idx_conversations_tenant_status', table_name='conversations')
    op.drop_index('idx_conversations_status', table_name='conversations')
    op.drop_index('idx_conversations_tenant', table_name='conversations')
    op.drop_table('conversations')
    op.drop_index('idx_agents_tenant_status', table_name='human_agents')
    op.drop_index('idx_agents_tenant', table_name='human_agents')
    op.drop_index('idx_agents_email', table_name='human_agents')
    op.drop_table('human_agents')
    op.drop_index('idx_knowledge_versions_tenant', table_name='knowledge_versions')
    op.drop_table('knowledge_versions')
    op.drop_index('idx_knowledge_sources_tenant', table_name='knowledge_sources')
    op.drop_table('knowledge_sources')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    op.drop_index('idx_assistants_tenant', table_name='assistants')
    op.drop_table('assistants')
    op.drop_table('workspaces')
    op.drop_table('tenants')
