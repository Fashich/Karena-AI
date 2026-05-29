"""
Karena AI Database Migrations
Migration 001: Initial schema creation
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Apply initial schema migration"""

    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(50), default="user"),
        sa.Column("department", sa.String(100)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # Create user_profiles table
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("preferences", sa.JSON(), default={}),
        sa.Column("conversation_history_summary", sa.Text()),
        sa.Column("expertise_areas", sa.ARRAY(sa.Text())),
        sa.Column("last_active_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("file_path", sa.String(1000)),
        sa.Column("file_type", sa.String(50)),
        sa.Column("file_size", sa.BigInteger()),
        sa.Column("source", sa.String(255)),
        sa.Column("metadata", sa.JSON(), default={}),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("indexed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("content_hash"),
    )

    # Create document_chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("document_id", sa.UUID(), sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding_vector", sa.Vector(768)),
        sa.Column("metadata", sa.JSON(), default={}),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "chunk_index"),
    )

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(500)),
        sa.Column("context_summary", sa.Text()),
        sa.Column("is_archived", sa.Boolean, default=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "conversation_id", sa.UUID(), sa.ForeignKey("conversations.id", ondelete="CASCADE")
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), default=[]),
        sa.Column("confidence_score", sa.Float()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("tokens_used", sa.Integer()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create audit_logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.UUID()),
        sa.Column("details", sa.JSON(), default={}),
        sa.Column("ip_address", sa.INET()),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create indexes
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_user_profiles_user_id", "user_profiles", ["user_id"])
    op.create_index("idx_documents_status", "documents", ["status"])
    op.create_index("idx_conversations_user_id", "conversations", ["user_id"])
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade():
    """Rollback initial schema migration"""

    op.drop_index("idx_audit_logs_created_at")
    op.drop_index("idx_audit_logs_user_id")
    op.drop_index("idx_messages_conversation_id")
    op.drop_index("idx_conversations_user_id")
    op.drop_index("idx_documents_status")
    op.drop_index("idx_user_profiles_user_id")
    op.drop_index("idx_users_role")
    op.drop_index("idx_users_email")

    op.drop_table("audit_logs")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("document_chunks")
    op.drop_table("documents")
    op.drop_table("user_profiles")
    op.drop_table("users")

    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
