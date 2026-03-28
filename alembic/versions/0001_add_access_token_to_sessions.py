"""check_in_sessions に access_token カラムを追加

Revision ID: 0001
Revises:
Create Date: 2026-03-29

既存DBへの適用手順:
  pip install -r requirements-dev.txt
  alembic upgrade head
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # access_token カラムを追加（既存行は NULL になる）
    op.add_column(
        "check_in_sessions",
        sa.Column("access_token", sa.String(36), nullable=True),
    )
    # 既存行に UUID を一括設定
    op.execute(
        """
        UPDATE check_in_sessions
        SET access_token = lower(hex(randomblob(4))) || '-'
                        || lower(hex(randomblob(2))) || '-4'
                        || substr(lower(hex(randomblob(2))), 2) || '-'
                        || substr('89ab', abs(random()) % 4 + 1, 1)
                        || substr(lower(hex(randomblob(2))), 2) || '-'
                        || lower(hex(randomblob(6)))
        WHERE access_token IS NULL
        """
    )
    # ユニーク制約とインデックスを付与
    op.create_index("ix_check_in_sessions_access_token", "check_in_sessions", ["access_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_check_in_sessions_access_token", table_name="check_in_sessions")
    op.drop_column("check_in_sessions", "access_token")
