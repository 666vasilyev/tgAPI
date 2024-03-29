"""Initial migration

Revision ID: 9445afa02886
Revises: 
Create Date: 2023-08-17 16:50:42.867437

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9445afa02886'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Channels',
    sa.Column('channel_id', sa.String(), nullable=False),
    sa.Column('type', sa.Enum('ul', 'l', 'n', 'r', 'ur', name='channeltype'), nullable=False),
    sa.PrimaryKeyConstraint('channel_id')
    )
    op.create_table('Posts',
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('channel_id', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.Column('media', sa.String(), nullable=False),
    sa.Column('reactions', sa.String(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['channel_id'], ['Channels.channel_id'], ),
    sa.PrimaryKeyConstraint('post_id')
    )
    op.create_table('Comments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['post_id'], ['Posts.post_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Comments')
    op.drop_table('Posts')
    op.drop_table('Channels')
    # ### end Alembic commands ###
