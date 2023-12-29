"""friendship model

Revision ID: 49d66dfbad6d
Revises: 104ebab9db5c
Create Date: 2023-12-22 18:51:37.926423

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '49d66dfbad6d'
down_revision: Union[str, None] = '104ebab9db5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('friendships',
    sa.Column('id_', sa.UUID(), nullable=False),
    sa.Column('requester_id', sa.UUID(), nullable=False),
    sa.Column('addressee_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Enum('sent', 'pending', 'declined', 'accepted', 'blocked', name='friendshipstatusenum'), nullable=False),
    sa.Column('request_date', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('accept_date', postgresql.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['addressee_id'], ['users.id_'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['requester_id'], ['users.id_'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id_')
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trigger_update_updated_at
        BEFORE UPDATE ON friendships
        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
        """
    )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP TRIGGER IF EXISTS trigger_update_updated_at ON friendships;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at;")
    op.drop_table('friendships')
    # ### end Alembic commands ###