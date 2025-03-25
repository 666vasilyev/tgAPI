"""deprecate channels and comments

Revision ID: 4c68285d3545
Revises: 
Create Date: 2025-02-18 14:00:56.762412

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4c68285d3545'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('Posts',
    sa.Column('post_id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('text', sa.String(), nullable=False),
    sa.Column('media', sa.String(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('post_id')
    )
    op.create_table('Proxies',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('addr', sa.String(), nullable=False),
    sa.Column('port', sa.Integer(), nullable=False),
    sa.Column('proxy_type', sa.Enum('HTTP', 'SOCKS4', 'SOCKS5', name='proxytype'), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('addr')
    )
    op.create_table('Accounts',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('login', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('requests', sa.Integer(), nullable=False),
    sa.Column('proxy_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['proxy_id'], ['Proxies.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('login')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Accounts')
    op.drop_table('Proxies')
    op.drop_table('Posts')
    # ### end Alembic commands ###
