import random
import logging
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="Asia/Tokyo")


def generate_daily_sessions():
    """平日のみ、9:00〜18:00 の間でランダムに3つのチェックイン時刻を生成してDBに保存する"""
    from app.database import SessionLocal
    from app.models import CheckInSession

    now = datetime.now()
    weekday = now.weekday()  # 0=月〜4=金, 5=土, 6=日
    if weekday >= 5:
        logger.info("Weekend - skipping session generation")
        return

    db = SessionLocal()
    try:
        today = now.date()
        # 既に今日のセッションが生成済みなら skip
        from sqlalchemy import func
        existing = (
            db.query(CheckInSession)
            .filter(func.date(CheckInSession.scheduled_at) == today)
            .count()
        )
        if existing >= 3:
            logger.info("Sessions already generated for today")
            return

        # 9:00〜18:00 (540〜1080分) の間でランダムに3つ
        minutes_pool = sorted(random.sample(range(540, 1080), 3))
        for m in minutes_pool:
            scheduled = datetime(today.year, today.month, today.day, m // 60, m % 60)
            session = CheckInSession(scheduled_at=scheduled, status="pending")
            db.add(session)
        db.commit()
        logger.info("Generated 3 check-in sessions for today: %s", [
            datetime(today.year, today.month, today.day, m // 60, m % 60).strftime("%H:%M")
            for m in minutes_pool
        ])
    except Exception as e:
        logger.error("Failed to generate sessions: %s", e)
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    if not _scheduler.running:
        # 毎朝0時05分に当日のセッションを生成
        _scheduler.add_job(
            generate_daily_sessions,
            CronTrigger(hour=0, minute=5, timezone="Asia/Tokyo"),
            id="daily_session_generator",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info("Scheduler started")
        # 起動時にも当日分を生成（起動が0時以降のケースに対応）
        generate_daily_sessions()


def stop_scheduler():
    if _scheduler.running:
        _scheduler.shutdown()
        logger.info("Scheduler stopped")
