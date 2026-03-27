"""
テスト共通フィクスチャ

テスト用 SQLite ファイル DB を使用し、各テスト関数の前後にテーブルを再作成することで
テスト間の状態汚染を防ぐ。

環境変数の上書きは app モジュールのインポートより先に行う。
"""
import os
import pytest
from datetime import datetime
from unittest.mock import patch

# ── テスト専用環境変数（app インポート前に設定する） ──────────────────────
os.environ["DATABASE_URL"] = "sqlite:////tmp/tancha_naran_do_test.db"
os.environ["LOG_DIR"] = "/tmp/tancha-test-logs"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import get_db
from app.models import Base, CheckInSession, CheckInAnswer, EmotionalScore
from app.main import app

_test_engine = create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
)
_TestSessionLocal = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def reset_db():
    """各テスト前にテーブルを再作成してクリーンな状態にする"""
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield


@pytest.fixture
def db_session():
    """テスト用 DB セッション（直接 DB 操作が必要なテスト向け）"""
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """FastAPI TestClient（スケジューラをモック化、get_db を テスト DB に差し替え）"""
    def override_get_db():
        db = _TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with patch("app.main.start_scheduler"), patch("app.main.stop_scheduler"):
        with TestClient(app, follow_redirects=False) as c:
            yield c

    app.dependency_overrides.clear()


# ── テストデータ生成ヘルパー ──────────────────────────────────────────────

def make_session(db, status="pending", started=False, completed=False):
    """CheckInSession を作成して返す"""
    session = CheckInSession(scheduled_at=datetime.now(), status=status)
    if started:
        session.started_at = datetime.now()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def make_completed_session(db):
    """回答済みスコア付き CheckInSession を作成して返す"""
    from app.scoring import calculate_scores

    session = make_session(db, status="completed", started=True, completed=True)
    session.completed_at = datetime.now()
    db.commit()

    answers_data = [{"question_id": i, "answer_value": 2} for i in range(1, 11)]
    for a in answers_data:
        db.add(CheckInAnswer(
            session_id=session.id,
            question_id=a["question_id"],
            answer_value=a["answer_value"],
            answered_at=datetime.now(),
        ))

    from datetime import date
    scores = calculate_scores(answers_data)
    db.add(EmotionalScore(
        session_id=session.id,
        date=date.today(),
        **scores,
    ))
    db.commit()
    db.refresh(session)
    return session
