"""
ロギング設定モジュール

出力先:
  - stdout          : アクセスログ・業務操作ログの両方
  - /data/logs/access.log : アクセスログ（RotatingFileHandler, 10MB x 5世代）
  - /data/logs/app.log    : 業務操作ログ（RotatingFileHandler, 10MB x 5世代）

ログレベルは環境変数 LOG_LEVEL（デフォルト: INFO）で制御する。
"""

import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path(os.getenv("LOG_DIR", "/data/logs"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)-20s %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """アプリケーション起動時に一度だけ呼び出す"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # ── stdout ハンドラー（全ロガー共通）──
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # ── app.log（業務操作ログ）──
    app_file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    app_file_handler.setFormatter(formatter)

    # ── access.log（アクセスログ）──
    access_file_handler = logging.handlers.RotatingFileHandler(
        LOG_DIR / "access.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    access_file_handler.setFormatter(formatter)

    # ルートロガー: stdout + app.log
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)
    if not root.handlers:
        root.addHandler(stream_handler)
        root.addHandler(app_file_handler)

    # アクセスロガー: stdout + access.log（ルートには伝播しない）
    access_logger = logging.getLogger("access")
    access_logger.setLevel(LOG_LEVEL)
    access_logger.propagate = False
    if not access_logger.handlers:
        access_logger.addHandler(stream_handler)
        access_logger.addHandler(access_file_handler)

    # uvicorn.error: 独自ハンドラーをクリアしてルートロガー経由で統一フォーマット出力
    uv_error = logging.getLogger("uvicorn.error")
    uv_error.handlers = []
    uv_error.propagate = True

    # uvicorn.access は AccessLogMiddleware で代替するため完全に無効化
    uv_access = logging.getLogger("uvicorn.access")
    uv_access.handlers = []
    uv_access.propagate = False
