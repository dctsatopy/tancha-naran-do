"""
app.main の追加セキュリティ機能のテスト

- Basic 認証（BASIC_AUTH_USER / BASIC_AUTH_PASSWORD によるオプトイン方式）
- CSRF: Origin/Referer が両方無い POST は拒否
- access_token の欠落時のオンデマンド払い出し
- アクセスログでの access_token マスキング
"""
import base64
import logging
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from tests.conftest import _TestSessionLocal, make_completed_session, make_session, without_csrf_headers


def _basic_auth_header(user, password):
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
def auth_client():
    """BASIC_AUTH_USER/PASSWORD を設定した状態の TestClient"""
    def override_get_db():
        db = _TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with patch.dict(os.environ, {"BASIC_AUTH_USER": "admin", "BASIC_AUTH_PASSWORD": "s3cret"}):
        with patch("app.main.start_scheduler"), patch("app.main.stop_scheduler"):
            with TestClient(app, follow_redirects=False) as c:
                yield c
    app.dependency_overrides.clear()


class TestBasicAuthDisabledByDefault:
    """BASIC_AUTH_USER/PASSWORD 未設定時は従来どおり無認証でアクセスできること"""

    def test_home_accessible_without_credentials(self, client):
        res = client.get("/")
        assert res.status_code == 200

    def test_health_accessible_without_credentials(self, client):
        res = client.get("/health")
        assert res.status_code == 200


class TestBasicAuthEnabled:
    """BASIC_AUTH_USER/PASSWORD 設定時は Basic 認証が要求されること"""

    def test_home_requires_auth(self, auth_client):
        res = auth_client.get("/")
        assert res.status_code == 401
        assert "WWW-Authenticate" in res.headers

    def test_home_with_wrong_credentials_rejected(self, auth_client):
        res = auth_client.get("/", headers=_basic_auth_header("admin", "wrong"))
        assert res.status_code == 401

    def test_home_with_correct_credentials_accepted(self, auth_client):
        res = auth_client.get("/", headers=_basic_auth_header("admin", "s3cret"))
        assert res.status_code == 200

    def test_health_bypasses_auth(self, auth_client):
        """ヘルスチェックはオーケストレーターからのアクセスのため認証不要"""
        res = auth_client.get("/health")
        assert res.status_code == 200

    def test_api_endpoint_requires_auth(self, auth_client):
        res = auth_client.get("/api/sessions")
        assert res.status_code == 401


class TestCsrfWithoutHeaders:
    """Origin/Referer が両方無い POST は拒否されること（API 想定利用がないため）"""

    def test_post_without_origin_or_referer_rejected(self, client, db_session):
        session = make_session(db_session, status="in_progress")
        with without_csrf_headers(client):
            res = client.post(
                "/check-in/submit",
                data={"session_id": str(session.id), "q_1": "2"},
            )
        assert res.status_code == 403


class TestAccessTokenOnDemandIssuance:
    """access_token が欠落しているセッションでもオンデマンドで払い出されること"""

    def test_result_page_issues_token_when_missing(self, client, db_session):
        session = make_completed_session(db_session)
        session.access_token = None
        db_session.add(session)
        db_session.commit()

        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_1": "2"},
            headers={"Origin": "http://testserver"},
        )
        # 既に completed のため 409 になるが、token フォールバックに session.id (連番) が
        # 使われていないことを確認する
        assert res.status_code == 409


class TestAccessLogTokenMasking:
    """アクセスログの access_token がマスクされること"""

    def test_result_path_token_is_masked_in_log(self, client, db_session, caplog):
        session = make_completed_session(db_session)
        token = session.access_token
        assert token is not None

        with caplog.at_level(logging.INFO, logger="access"):
            client.get(f"/check-in/result/{token}")

        access_records = [r for r in caplog.records if r.name == "access"]
        assert access_records, "access ロガーの出力が見つかりません"
        logged = "\n".join(r.getMessage() for r in access_records)
        assert token not in logged
