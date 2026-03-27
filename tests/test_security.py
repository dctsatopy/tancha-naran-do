"""
セキュリティ関連のテスト

- HTTP セキュリティヘッダーの検証
- API ドキュメント非公開の確認
- 入力バリデーションの確認
仕様参照: fix/security-hardening コミット
"""
import pytest
from tests.conftest import make_session

SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "x-xss-protection": "1; mode=block",
    "referrer-policy": "strict-origin-when-cross-origin",
}


class TestSecurityHeaders:
    """全エンドポイントでセキュリティヘッダーが付与されること"""

    @pytest.mark.parametrize("path", [
        "/",
        "/check-in",
        "/dashboard",
        "/api/status",
        "/api/history",
        "/api/sessions",
    ])
    def test_security_headers_present(self, client, path):
        """各エンドポイントで全セキュリティヘッダーが返ること"""
        res = client.get(path)
        for header, expected_value in SECURITY_HEADERS.items():
            actual = res.headers.get(header)
            assert actual == expected_value, (
                f"path={path}: {header} = {actual!r}, expected {expected_value!r}"
            )

    def test_security_headers_on_404(self, client):
        """404 レスポンスにもセキュリティヘッダーが付与されること"""
        res = client.get("/nonexistent-page")
        for header, expected_value in SECURITY_HEADERS.items():
            assert res.headers.get(header) == expected_value

    def test_security_headers_on_post(self, client):
        """POST レスポンスにもセキュリティヘッダーが付与されること"""
        res = client.post("/check-in/submit", data={"session_id": "0"})
        for header, expected_value in SECURITY_HEADERS.items():
            assert res.headers.get(header) == expected_value


class TestApiDocumentationDisabled:
    """API ドキュメントが非公開であること（ENABLE_DOCS=false デフォルト）"""

    def test_docs_endpoint_disabled(self, client):
        """GET /docs が 404 を返すこと"""
        res = client.get("/docs")
        assert res.status_code == 404

    def test_redoc_endpoint_disabled(self, client):
        """GET /redoc が 404 を返すこと"""
        res = client.get("/redoc")
        assert res.status_code == 404

    def test_openapi_json_disabled(self, client):
        """GET /openapi.json が 404 を返すこと"""
        res = client.get("/openapi.json")
        assert res.status_code == 404


class TestInputValidationSessionId:
    """session_id の入力バリデーション"""

    @pytest.mark.parametrize("session_id_value", [
        "abc",        # 非数値
        "1.5",        # 小数
        "",           # 空文字
        "0",          # ゼロ
        "-1",         # 負値
        "<script>",   # XSS 試行
    ])
    def test_invalid_session_id_returns_400(self, client, session_id_value):
        """不正な session_id は 400 を返すこと"""
        res = client.post(
            "/check-in/submit",
            data={"session_id": session_id_value, "q_1": "2"},
        )
        assert res.status_code == 400, f"session_id={session_id_value!r} should return 400"


class TestInputValidationAnswerValue:
    """answer_value の入力バリデーション"""

    @pytest.mark.parametrize("answer_value", ["0", "5", "100", "-1", "abc"])
    def test_invalid_answer_value_returns_400(self, client, db_session, answer_value):
        """1〜4 以外の回答値は 400 を返すこと"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_1": answer_value},
        )
        assert res.status_code == 400, f"answer_value={answer_value!r} should return 400"

    @pytest.mark.parametrize("answer_value", ["1", "2", "3", "4"])
    def test_valid_answer_value_accepted(self, client, db_session, answer_value):
        """1〜4 の回答値は受け付けられること"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_1": answer_value},
        )
        # 400 でなければ OK（404 はセッション存在確認の都合で起きうる）
        assert res.status_code != 400


class TestInputValidationQuestionId:
    """question_id の入力バリデーション"""

    def test_unknown_question_id_returns_400(self, client, db_session):
        """存在しない question_id は 400 を返すこと"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_9999": "2"},
        )
        assert res.status_code == 400

    def test_question_id_0_returns_400(self, client, db_session):
        """question_id=0 は 400 を返すこと"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_0": "2"},
        )
        assert res.status_code == 400

    def test_question_id_201_returns_400(self, client, db_session):
        """question_id=201 は 400 を返すこと"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_201": "2"},
        )
        assert res.status_code == 400


class TestApiParameterBounds:
    """API パラメータの上限・下限バリデーション"""

    @pytest.mark.parametrize("days,expected_status", [
        (1, 200),    # 下限境界値
        (7, 200),    # デフォルト
        (30, 200),   # 仕様の30日
        (365, 200),  # 上限境界値
        (366, 422),  # 上限超過
        (0, 422),    # 下限未満
        (-1, 422),   # 負値
    ])
    def test_history_days_param(self, client, days, expected_status):
        res = client.get(f"/api/history?days={days}")
        assert res.status_code == expected_status

    @pytest.mark.parametrize("limit,expected_status", [
        (1, 200),    # 下限境界値
        (20, 200),   # デフォルト
        (200, 200),  # 上限境界値
        (201, 422),  # 上限超過
        (0, 422),    # 下限未満
    ])
    def test_sessions_limit_param(self, client, limit, expected_status):
        res = client.get(f"/api/sessions?limit={limit}")
        assert res.status_code == expected_status
