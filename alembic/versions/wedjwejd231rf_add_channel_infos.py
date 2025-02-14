from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from src.db.channels_table import channels_table
from src.db.models import Channel

# Revision identifiers, used by Alembic.
revision = 'wedjwejd231rf'
down_revision = '2da2cd88462b'  # Укажите ID предыдущей миграции, если есть
branch_labels = None
depends_on = None

def upgrade():
    """Заполняет таблицу 'channels' данными."""
    bind = op.get_bind()
    session = sa.orm.Session(bind)
    try:
        for url, channel_type in channels_table:
            stmt = insert(Channel).values(channel_id=url, type=channel_type).on_conflict_do_nothing()
            session.execute(stmt)
        session.commit()
    except IntegrityError:
        session.rollback()
        print('Table "Channels" already contains the data.')
    finally:
        session.close()

def downgrade():
    """Очищает таблицу 'channels' от данных, добавленных в этой миграции."""
    bind = op.get_bind()
    session = sa.orm.Session(bind)
    session.query(Channel).delete()
    session.commit()
    session.close()
