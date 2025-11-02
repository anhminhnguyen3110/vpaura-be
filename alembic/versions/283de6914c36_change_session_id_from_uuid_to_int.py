"""change_session_id_from_uuid_to_int

Revision ID: 283de6914c36
Revises: 001
Create Date: 2025-11-03 02:18:55.655501

This migration changes Session.id from UUID to INTEGER with auto-increment.
This is a breaking change that requires data migration.

IMPORTANT: This will drop and recreate tables, losing all existing data.
For production, you would need a more sophisticated migration strategy.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '283de6914c36'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change sessions.id from UUID to INTEGER with auto-increment.
    
    WARNING: This is a destructive migration that will:
    1. Drop all foreign key constraints
    2. Drop dependent tables (messages, session_documents)
    3. Drop sessions table
    4. Recreate all tables with INTEGER id
    
    For production, you would need to:
    - Export existing data
    - Create mapping from UUID to new INTEGER ids
    - Re-import data with new ids
    """
    
    # Step 1: Drop foreign key constraints and dependent tables (if they exist)
    op.execute("DROP TABLE IF EXISTS messages CASCADE")
    op.execute("DROP TABLE IF EXISTS session_documents CASCADE")
    
    # Step 2: Drop sessions table (if exists)
    op.execute("DROP TABLE IF EXISTS sessions CASCADE")
    
    # Step 3: Recreate sessions table with INTEGER id
    op.create_table(
        'sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Step 4: Create MessageRole enum if it doesn't exist
    # PostgreSQL doesn't support CREATE TYPE IF NOT EXISTS, so we check first
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE messagerole AS ENUM ('USER', 'ASSISTANT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Step 5: Recreate messages table with INTEGER session_id
    # Note: Using postgresql.ENUM with create_type=False to reuse existing enum
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('role', postgresql.ENUM('USER', 'ASSISTANT', name='messagerole', create_type=False), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("role IN ('USER', 'ASSISTANT')", name='check_message_role_business_only'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_session_created', 'messages', ['session_id', 'created_at'], unique=False)
    
    # Step 6: Recreate session_documents junction table with INTEGER session_id
    op.create_table(
        'session_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """
    Revert back to UUID-based sessions.id.
    
    WARNING: This is also destructive and will lose all data.
    """
    
    # Step 1: Drop foreign key constraints and dependent tables
    op.drop_index('ix_messages_session_created', table_name='messages')
    op.drop_table('messages')
    op.drop_table('session_documents')
    
    # Step 2: Drop sessions table
    op.drop_table('sessions')
    
    # Step 3: Recreate sessions table with UUID id
    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Step 4: Recreate messages table with UUID session_id
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('role', sa.Enum('USER', 'ASSISTANT', name='messagerole'), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('extra_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='check_message_role_business_only'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_messages_session_created', 'messages', ['session_id', 'created_at'], unique=False)
    
    # Step 5: Recreate session_documents junction table with UUID session_id
    op.create_table(
        'session_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
