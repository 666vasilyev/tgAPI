"""create tables

Revision ID: c6e46d199f11
Revises: 
Create Date: 2023-04-09 18:11:16.765710

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c6e46d199f11"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "proxies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("addr", sa.String(), nullable=False),
        sa.Column("port", sa.Integer(), nullable=False),
        sa.Column(
            "proxy_type",
            sa.Enum("HTTPS", "SOCKS4", "SOCKS5", name="proxytype"),
            nullable=False,
        ),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("addr"),
    )
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("celery_id", sa.String(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PENDING", "DONE", "ERROR", name="taskstatus"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("login", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("proxy_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["proxy_id"], ["proxies.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("login"),
    )
    op.create_table(
        "parsing_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column(
            "date_parsed",
            sa.DateTime(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("result", sa.String(), nullable=False),
        sa.Column(
            "status", sa.Enum("FAILURE", "SUCCESS", name="resultstatus"), nullable=False
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("parsing_results")
    op.drop_table("accounts")
    op.drop_table("tasks")
    op.drop_table("proxies")
    # ### end Alembic commands ###