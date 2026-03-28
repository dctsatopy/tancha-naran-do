"""
スケジューラ (app/scheduler.py) のユニットテスト

仕様参照: tancha_naran_do.md §3.1, §3.4
- 平日（月〜金）9:00〜18:00 の間に1日3回のチェックイン時刻を生成
- 土日はスキップ
- 既に3件以上生成済みの場合はスキップ
"""
import pytest
from datetime import datetime, date
from unittest.mock import patch
from freezegun import freeze_time

from app.scheduler import generate_daily_sessions, generate_weekend_session
from app.models import CheckInSession


class TestGenerateDailySessions:
    """generate_daily_sessions() の動作検証"""

    @freeze_time("2026-03-30 00:05:00")  # 月曜日
    def test_generates_3_sessions_on_weekday(self, db_session):
        """平日に3つのセッションが生成されること（仕様 §3.1）"""
        generate_daily_sessions()
        count = db_session.query(CheckInSession).count()
        assert count == 3

    @freeze_time("2026-03-30 00:05:00")
    def test_sessions_status_is_pending(self, db_session):
        """生成されたセッションの status が pending であること"""
        generate_daily_sessions()
        sessions = db_session.query(CheckInSession).all()
        for s in sessions:
            assert s.status == "pending", f"session_id={s.id} status={s.status}"

    @freeze_time("2026-03-30 00:05:00")
    def test_sessions_scheduled_in_work_hours(self, db_session):
        """セッション時刻が 9:00〜18:00 の範囲内であること（仕様 §3.1）"""
        generate_daily_sessions()
        sessions = db_session.query(CheckInSession).all()
        for s in sessions:
            t = s.scheduled_at.time()
            assert t >= datetime.strptime("09:00", "%H:%M").time(), \
                f"session_id={s.id}: {t} は 9:00 より前"
            assert t < datetime.strptime("18:00", "%H:%M").time(), \
                f"session_id={s.id}: {t} は 18:00 以降"

    @freeze_time("2026-03-30 00:05:00")
    def test_sessions_scheduled_on_today(self, db_session):
        """生成されたセッションの日付が今日であること"""
        generate_daily_sessions()
        sessions = db_session.query(CheckInSession).all()
        today = date(2026, 3, 30)
        for s in sessions:
            assert s.scheduled_at.date() == today

    @freeze_time("2026-03-30 00:05:00")
    def test_sessions_times_are_unique(self, db_session):
        """生成された3セッションの時刻が重複しないこと"""
        generate_daily_sessions()
        sessions = db_session.query(CheckInSession).all()
        times = [s.scheduled_at for s in sessions]
        assert len(set(times)) == 3

    @freeze_time("2026-03-28 00:05:00")  # 土曜日
    def test_skips_on_saturday(self, db_session):
        """土曜日はセッションを生成しないこと（仕様 §3.1）"""
        generate_daily_sessions()
        count = db_session.query(CheckInSession).count()
        assert count == 0

    @freeze_time("2026-03-29 00:05:00")  # 日曜日
    def test_skips_on_sunday(self, db_session):
        """日曜日はセッションを生成しないこと（仕様 §3.1）"""
        generate_daily_sessions()
        count = db_session.query(CheckInSession).count()
        assert count == 0

    @freeze_time("2026-03-30 00:05:00")
    def test_does_not_duplicate_when_already_3_sessions(self, db_session):
        """既に3セッション生成済みの場合は重複生成しないこと"""
        generate_daily_sessions()
        generate_daily_sessions()  # 2回目
        count = db_session.query(CheckInSession).count()
        assert count == 3, "2回目の呼び出しで重複生成されました"

    @freeze_time("2026-03-30 00:05:00")
    def test_times_are_sorted_ascending(self, db_session):
        """生成されたセッション時刻が昇順であること（ユーザー体験上の期待値）"""
        generate_daily_sessions()
        sessions = (
            db_session.query(CheckInSession)
            .order_by(CheckInSession.scheduled_at)
            .all()
        )
        times = [s.scheduled_at for s in sessions]
        assert times == sorted(times)

    @pytest.mark.parametrize("weekday_date,weekday_name", [
        ("2026-03-30 00:05:00", "月曜"),
        ("2026-03-31 00:05:00", "火曜"),
        ("2026-04-01 00:05:00", "水曜"),
        ("2026-04-02 00:05:00", "木曜"),
        ("2026-04-03 00:05:00", "金曜"),
    ])
    def test_generates_on_all_weekdays(self, db_session, weekday_date, weekday_name):
        """月〜金の全曜日でセッションが生成されること"""
        with freeze_time(weekday_date):
            generate_daily_sessions()
        count = db_session.query(CheckInSession).count()
        assert count == 3, f"{weekday_name}: 3セッション生成されませんでした (count={count})"


class TestGenerateWeekendSession:
    """generate_weekend_session() の動作検証（仕様 §3.5）"""

    @freeze_time("2026-03-28 10:00:00")  # 土曜日
    def test_generates_1_session_on_saturday(self, db_session):
        """土曜日に1件のセッションが生成されること"""
        generate_weekend_session()
        assert db_session.query(CheckInSession).count() == 1

    @freeze_time("2026-03-29 10:00:00")  # 日曜日
    def test_generates_1_session_on_sunday(self, db_session):
        """日曜日に1件のセッションが生成されること"""
        generate_weekend_session()
        assert db_session.query(CheckInSession).count() == 1

    @freeze_time("2026-03-28 10:00:00")
    def test_session_scheduled_in_evening_hours(self, db_session):
        """生成セッションの時刻が 18:00〜21:00 の範囲内であること（仕様 §3.5）"""
        generate_weekend_session()
        s = db_session.query(CheckInSession).first()
        t = s.scheduled_at.time()
        assert t >= datetime.strptime("18:00", "%H:%M").time(), f"{t} は 18:00 より前"
        assert t < datetime.strptime("21:00", "%H:%M").time(), f"{t} は 21:00 以降"

    @freeze_time("2026-03-28 10:00:00")
    def test_session_status_is_pending(self, db_session):
        """生成セッションの status が pending であること"""
        generate_weekend_session()
        s = db_session.query(CheckInSession).first()
        assert s.status == "pending"

    @freeze_time("2026-03-30 10:00:00")  # 月曜日
    def test_skips_on_weekday(self, db_session):
        """平日はセッションを生成しないこと"""
        generate_weekend_session()
        assert db_session.query(CheckInSession).count() == 0

    @freeze_time("2026-03-28 10:00:00")
    def test_no_duplicate_on_second_call(self, db_session):
        """既に1件あれば2回目の呼び出しで重複生成しないこと"""
        generate_weekend_session()
        generate_weekend_session()
        assert db_session.query(CheckInSession).count() == 1
