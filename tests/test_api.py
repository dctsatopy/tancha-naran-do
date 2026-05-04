"""
HTTP エンドポイントの統合テスト (app/main.py)

仕様参照: tancha_naran_do.md §3, §6, §9
"""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from app.models import CheckInSession, EmotionalScore
from tests.conftest import make_session, make_completed_session


class TestHomeEndpoint:
    """GET / — ホーム画面"""

    def test_returns_200(self, client):
        res = client.get("/")
        assert res.status_code == 200

    def test_returns_html(self, client):
        res = client.get("/")
        assert "text/html" in res.headers["content-type"]

    def test_contains_app_title(self, client):
        res = client.get("/")
        assert "たんちゃーならんど" in res.text

    def test_shows_check_in_link(self, client):
        res = client.get("/")
        assert "/check-in" in res.text

    @freeze_time("2026-03-28 09:00:00")  # 土曜日
    def test_weekend_prompt_shown_when_no_sessions(self, client):
        """土日にセッションが0件のとき週末プロンプトモーダルが表示されること（仕様 §3.5）"""
        res = client.get("/")
        assert res.status_code == 200
        assert "weekendModal" in res.text

    @freeze_time("2026-03-30 09:00:00")  # 月曜日
    def test_weekend_prompt_not_shown_on_weekday(self, client):
        """平日はプロンプトモーダルが表示されないこと"""
        res = client.get("/")
        assert "weekendModal" not in res.text

    @freeze_time("2026-03-28 09:00:00")  # 土曜日
    def test_weekend_prompt_not_shown_when_session_exists(self, client, db_session):
        """土日でもセッションが存在する場合はプロンプトを表示しないこと"""
        make_session(db_session)
        res = client.get("/")
        assert "weekendModal" not in res.text


class TestCheckInPageEndpoint:
    """GET /check-in — チェックイン画面"""

    def test_new_session_created_when_no_session_id(self, client, db_session):
        """session_id なしでアクセスすると新しいセッションが作成されること"""
        before = db_session.query(CheckInSession).count()
        res = client.get("/check-in")
        after = db_session.query(CheckInSession).count()
        assert res.status_code == 200
        assert after == before + 1

    def test_returns_html_with_questions(self, client):
        """チェックイン画面に設問フォームが含まれること"""
        res = client.get("/check-in")
        assert res.status_code == 200
        assert "check-in-form" in res.text
        assert 'name="session_id"' in res.text

    def test_10_questions_shown(self, client):
        """1 セッションあたり 10 問が表示されること（仕様 §3.1）"""
        res = client.get("/check-in")
        # radio ボタン input の name="q_XXX" の数をカウント
        import re
        question_names = set(re.findall(r'name="(q_\d+)"', res.text))
        assert len(question_names) == 10

    def test_session_id_in_hidden_field(self, client):
        """hidden フィールドに session_id が含まれること"""
        import re
        res = client.get("/check-in")
        assert re.search(r'name="session_id"\s+value="\d+"', res.text)

    def test_existing_session_id(self, client, db_session):
        """有効な session_id を渡すと既存セッションが使われること"""
        session = make_session(db_session, status="pending")
        res = client.get(f"/check-in?session_id={session.id}")
        assert res.status_code == 200

    def test_invalid_session_id_returns_404(self, client):
        """存在しない session_id は 404 になること"""
        res = client.get("/check-in?session_id=99999")
        assert res.status_code == 404

    def test_completed_session_redirects_to_result(self, client, db_session):
        """完了済みセッションでアクセスすると結果画面にリダイレクトされること（access_token ベースURL）"""
        session = make_completed_session(db_session)
        res = client.get(f"/check-in?session_id={session.id}")
        assert res.status_code == 307  # または 302/303
        assert f"/check-in/result/{session.access_token}" in res.headers["location"]

    def test_session_id_zero_returns_404(self, client):
        """session_id=0 は 404 になること（is not None チェック）"""
        res = client.get("/check-in?session_id=0")
        assert res.status_code == 404

    def test_same_session_shows_same_questions_on_reload(self, client):
        """同一 session_id での再アクセス時に同じ問題セットが表示されること（仕様 §3.1）"""
        import re
        res1 = client.get("/check-in")
        match = re.search(r'name="session_id"\s+value="(\d+)"', res1.text)
        assert match, "session_id が見つかりません"
        session_id = match.group(1)
        q_names_1 = set(re.findall(r'name="(q_\d+)"', res1.text))

        res2 = client.get(f"/check-in?session_id={session_id}")
        q_names_2 = set(re.findall(r'name="(q_\d+)"', res2.text))

        assert q_names_1 == q_names_2, "再アクセス時に問題セットが変わっています"

    def test_session_status_becomes_in_progress(self, client, db_session):
        """チェックイン画面を開くと status が in_progress になること"""
        session = make_session(db_session, status="pending")
        client.get(f"/check-in?session_id={session.id}")
        db_session.refresh(session)
        assert session.status == "in_progress"


class TestSubmitEndpoint:
    """POST /check-in/submit — 回答送信"""

    def _valid_form(self, session_id: int, question_ids: list[int]) -> dict:
        data = {"session_id": str(session_id)}
        for qid in question_ids:
            data[f"q_{qid}"] = "2"
        return data

    def test_valid_submission_redirects_to_result(self, client, db_session):
        """有効な回答送信は 303 リダイレクトになること（access_token ベース URL）"""
        session = make_session(db_session, status="in_progress")
        form = self._valid_form(session.id, list(range(1, 11)))
        res = client.post("/check-in/submit", data=form)
        assert res.status_code == 303
        db_session.refresh(session)
        assert f"/check-in/result/{session.access_token}" in res.headers["location"]

    def test_valid_submission_completes_session(self, client, db_session):
        """有効な送信でセッション status が completed になること"""
        session = make_session(db_session, status="in_progress")
        form = self._valid_form(session.id, list(range(1, 11)))
        client.post("/check-in/submit", data=form)
        db_session.refresh(session)
        assert session.status == "completed"

    def test_valid_submission_saves_answers(self, client, db_session):
        """回答が DB に保存されること"""
        from app.models import CheckInAnswer
        session = make_session(db_session, status="in_progress")
        form = self._valid_form(session.id, list(range(1, 11)))
        client.post("/check-in/submit", data=form)
        count = db_session.query(CheckInAnswer).filter_by(session_id=session.id).count()
        assert count == 10

    def test_valid_submission_saves_score(self, client, db_session):
        """スコアが DB に保存されること"""
        session = make_session(db_session, status="in_progress")
        form = self._valid_form(session.id, list(range(1, 11)))
        client.post("/check-in/submit", data=form)
        score = db_session.query(EmotionalScore).filter_by(session_id=session.id).first()
        assert score is not None
        assert 0.0 <= score.overall_score <= 100.0

    def test_invalid_session_id_non_numeric_returns_400(self, client):
        """非数値の session_id は 400 になること"""
        res = client.post("/check-in/submit", data={"session_id": "abc", "q_1": "2"})
        assert res.status_code == 400

    def test_invalid_session_id_zero_returns_400(self, client):
        """session_id=0 は 400 になること"""
        res = client.post("/check-in/submit", data={"session_id": "0", "q_1": "2"})
        assert res.status_code == 400

    def test_nonexistent_session_id_returns_404(self, client):
        """存在しない session_id は 404 になること"""
        res = client.post("/check-in/submit", data={"session_id": "99999", "q_1": "2"})
        assert res.status_code == 404

    def test_invalid_answer_value_returns_400(self, client, db_session):
        """回答値が 1〜4 の範囲外は 400 になること"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_1": "5"},
        )
        assert res.status_code == 400

    def test_zero_answer_value_returns_400(self, client, db_session):
        """回答値 0 は 400 になること"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_1": "0"},
        )
        assert res.status_code == 400

    def test_unknown_question_id_returns_400(self, client, db_session):
        """存在しない question_id は 400 になること"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_9999": "2"},
        )
        assert res.status_code == 400

    def test_non_numeric_question_id_returns_400(self, client, db_session):
        """非数値の question_id フィールド名は 400 になること"""
        session = make_session(db_session, status="in_progress")
        res = client.post(
            "/check-in/submit",
            data={"session_id": str(session.id), "q_abc": "2"},
        )
        assert res.status_code == 400

    def test_double_submission_returns_409(self, client, db_session):
        """完了済みセッションへの再送信は 409 になること（仕様 §11.2）"""
        session = make_session(db_session, status="in_progress")
        form = self._valid_form(session.id, list(range(1, 11)))
        client.post("/check-in/submit", data=form)  # 1回目（正常）
        res = client.post("/check-in/submit", data=form)  # 2回目（重複）
        assert res.status_code == 409

    def test_concurrent_submission_no_duplicate_scores(self, client, db_session):
        """並行送信でスコアが重複保存されないこと（仕様 §11.2）"""
        import concurrent.futures
        from app.models import EmotionalScore

        session = make_session(db_session, status="in_progress")
        form = self._valid_form(session.id, list(range(1, 11)))

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(client.post, "/check-in/submit", data=form) for _ in range(3)]
            status_codes = [f.result().status_code for f in concurrent.futures.as_completed(futures)]

        # 成功（303）は最大1件、残りは 409
        success_count = sum(1 for s in status_codes if s == 303)
        assert success_count <= 1, f"複数の成功レスポンスが返りました: {status_codes}"

        # DB でスコアが1件以下であることを確認（重複保存なし）
        score_count = db_session.query(EmotionalScore).filter_by(session_id=session.id).count()
        assert score_count <= 1, f"スコアが重複保存されました: {score_count}件"


class TestResultEndpoint:
    """GET /check-in/result/{access_token} — 結果画面"""

    def test_returns_200_for_completed_session(self, client, db_session):
        """完了済みセッションで結果画面が表示されること"""
        session = make_completed_session(db_session)
        res = client.get(f"/check-in/result/{session.access_token}")
        assert res.status_code == 200

    def test_returns_html(self, client, db_session):
        session = make_completed_session(db_session)
        res = client.get(f"/check-in/result/{session.access_token}")
        assert "text/html" in res.headers["content-type"]

    def test_contains_score(self, client, db_session):
        """スコアが表示されること"""
        session = make_completed_session(db_session)
        res = client.get(f"/check-in/result/{session.access_token}")
        assert "点" in res.text

    def test_invalid_token_returns_404(self, client):
        """存在しないアクセストークンは 404 になること"""
        res = client.get("/check-in/result/00000000-0000-0000-0000-000000000000")
        assert res.status_code == 404


class TestDashboardEndpoint:
    """GET /dashboard — ダッシュボード画面"""

    def test_returns_200(self, client):
        res = client.get("/dashboard")
        assert res.status_code == 200

    def test_returns_html(self, client):
        res = client.get("/dashboard")
        assert "text/html" in res.headers["content-type"]

    def test_contains_chart_elements(self, client):
        """グラフ用 canvas 要素が含まれること（仕様 §3.2）"""
        res = client.get("/dashboard")
        assert "overallChart" in res.text
        assert "radarChart" in res.text


class TestApiStatusEndpoint:
    """GET /api/status — チェックイン状態確認（ポーリング用）"""

    def test_returns_200(self, client):
        res = client.get("/api/status")
        assert res.status_code == 200

    def test_returns_json(self, client):
        res = client.get("/api/status")
        assert res.headers["content-type"].startswith("application/json")

    def test_no_pending_session_returns_false(self, client):
        """pending セッションがない場合 check_in_ready=False"""
        data = client.get("/api/status").json()
        assert data["check_in_ready"] is False

    def test_pending_session_in_window_returns_true(self, client, db_session):
        """現在時刻の5分前〜現在に pending セッションがあると check_in_ready=True"""
        now = datetime.now()
        session = CheckInSession(
            scheduled_at=now - timedelta(minutes=2),
            status="pending",
        )
        db_session.add(session)
        db_session.commit()

        data = client.get("/api/status").json()
        assert data["check_in_ready"] is True
        assert data["session_id"] == session.id

    def test_future_session_not_ready(self, client, db_session):
        """未来のセッションは check_in_ready=False であること"""
        future = datetime.now() + timedelta(hours=1)
        db_session.add(CheckInSession(scheduled_at=future, status="pending"))
        db_session.commit()

        data = client.get("/api/status").json()
        assert data["check_in_ready"] is False


class TestApiHistoryEndpoint:
    """GET /api/history — グラフ用データ"""

    def test_returns_200(self, client):
        res = client.get("/api/history")
        assert res.status_code == 200

    def test_returns_json_list(self, client):
        data = client.get("/api/history").json()
        assert isinstance(data, list)

    def test_empty_when_no_scores(self, client):
        """スコアがない場合は空リストが返ること"""
        data = client.get("/api/history").json()
        assert data == []

    def test_days_param_default_7(self, client, db_session):
        """デフォルト days=7 で動作すること"""
        res = client.get("/api/history")
        assert res.status_code == 200

    def test_days_param_30(self, client):
        """days=30 が受け付けられること"""
        res = client.get("/api/history?days=30")
        assert res.status_code == 200

    def test_days_param_max_365(self, client):
        """days=365 が受け付けられること（上限境界値）"""
        res = client.get("/api/history?days=365")
        assert res.status_code == 200

    def test_days_param_over_limit_returns_422(self, client):
        """days>365 は 422 になること（入力検証）"""
        res = client.get("/api/history?days=366")
        assert res.status_code == 422

    def test_days_param_zero_returns_422(self, client):
        """days=0 は 422 になること"""
        res = client.get("/api/history?days=0")
        assert res.status_code == 422

    def test_response_structure(self, client, db_session):
        """レスポンスの各要素に必要なキーが含まれること"""
        session = make_completed_session(db_session)
        data = client.get("/api/history?days=7").json()
        if data:
            entry = data[0]
            for key in ["date", "overall", "anger_state", "cognitive_pattern", "physiological", "behavioral", "emotion_regulation", "psychological_state"]:
                assert key in entry, f"'{key}' キーが見つかりません"


class TestApiSessionsEndpoint:
    """GET /api/sessions — セッション一覧"""

    def test_returns_200(self, client):
        res = client.get("/api/sessions")
        assert res.status_code == 200

    def test_returns_json_list(self, client):
        data = client.get("/api/sessions").json()
        assert isinstance(data, list)

    def test_limit_default_20(self, client):
        """デフォルト limit=20 が動作すること"""
        res = client.get("/api/sessions")
        assert res.status_code == 200

    def test_limit_max_200(self, client):
        """limit=200 が受け付けられること（上限境界値）"""
        res = client.get("/api/sessions?limit=200")
        assert res.status_code == 200

    def test_limit_over_max_returns_422(self, client):
        """limit=201 は 422 になること"""
        res = client.get("/api/sessions?limit=201")
        assert res.status_code == 422

    def test_limit_zero_returns_422(self, client):
        """limit=0 は 422 になること"""
        res = client.get("/api/sessions?limit=0")
        assert res.status_code == 422

    def test_session_response_structure(self, client, db_session):
        """レスポンスの各要素に必要なキーが含まれること"""
        make_session(db_session)
        data = client.get("/api/sessions").json()
        assert len(data) > 0
        session_item = data[0]
        for key in ["id", "scheduled_at", "status"]:
            assert key in session_item


class TestApiWeekendSessionEndpoint:
    """POST /api/sessions/weekend — 土日振り返りセッション生成（仕様 §3.5）"""

    @freeze_time("2026-03-28 10:00:00")  # 土曜日
    def test_creates_session_on_saturday(self, client):
        """土曜日にセッションを作成できること"""
        res = client.post("/api/sessions/weekend")
        assert res.status_code == 200

    @freeze_time("2026-03-29 10:00:00")  # 日曜日
    def test_creates_session_on_sunday(self, client):
        """日曜日にセッションを作成できること"""
        res = client.post("/api/sessions/weekend")
        assert res.status_code == 200

    @freeze_time("2026-03-28 10:00:00")
    def test_response_has_required_fields(self, client):
        """レスポンスに session_id と scheduled_at が含まれること"""
        data = client.post("/api/sessions/weekend").json()
        assert "session_id" in data
        assert "scheduled_at" in data

    @freeze_time("2026-03-28 10:00:00")
    def test_session_scheduled_in_evening_hours(self, client):
        """生成セッションの時刻が 18:00〜21:00 の範囲内であること"""
        data = client.post("/api/sessions/weekend").json()
        from datetime import datetime as dt
        t = dt.fromisoformat(data["scheduled_at"]).time()
        assert t >= dt.strptime("18:00", "%H:%M").time(), f"{t} は 18:00 より前"
        assert t < dt.strptime("21:00", "%H:%M").time(), f"{t} は 21:00 以降"

    @freeze_time("2026-03-30 10:00:00")  # 月曜日
    def test_returns_400_on_weekday(self, client):
        """平日は 400 を返すこと"""
        res = client.post("/api/sessions/weekend")
        assert res.status_code == 400

    @freeze_time("2026-03-28 10:00:00")
    def test_duplicate_returns_409(self, client):
        """既にセッションがある場合は 409 を返すこと"""
        client.post("/api/sessions/weekend")  # 1回目
        res = client.post("/api/sessions/weekend")  # 2回目
        assert res.status_code == 409

    @freeze_time("2026-03-28 10:00:00")
    def test_security_headers_present(self, client):
        """セキュリティヘッダーが付与されること"""
        res = client.post("/api/sessions/weekend")
        assert res.headers.get("x-content-type-options") == "nosniff"
