"""tests/conftest.py のテストヘルパーに対するテスト"""
from tests.conftest import without_csrf_headers


class TestWithoutCsrfHeaders:
    """without_csrf_headers: client のデフォルト Origin ヘッダーを一時的に取り除けること"""

    def test_removes_and_restores_origin_header(self, client):
        assert client.headers.get("origin") is not None
        with without_csrf_headers(client):
            assert client.headers.get("origin") is None
        assert client.headers.get("origin") is not None
