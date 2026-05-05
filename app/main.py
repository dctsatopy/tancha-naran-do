import os
import uuid
import time
import secrets
import random
import logging
from datetime import datetime, date, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import engine, get_db
from app.models import Base, CheckInSession, CheckInAnswer, EmotionalScore
from app.questions_data import QUESTIONS, QUESTION_BY_ID
from app.messages_data import get_random_message, get_messages
from app.scoring import calculate_scores, get_score_label
from app.scheduler import start_scheduler, stop_scheduler
from app.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")

# 本番環境では API ドキュメントを非公開にする（ENABLE_DOCS=true で有効化）
_ENABLE_DOCS = os.getenv("ENABLE_DOCS", "false").lower() == "true"

VALID_ANSWER_VALUES = {1, 2, 3, 4}

# ── レート制限 ────────────────────────────────────────────────────────────────
# DISABLE_RATE_LIMIT=true でテスト時などに無効化できる
_RATE_LIMIT_ENABLED = os.getenv("DISABLE_RATE_LIMIT", "false").lower() != "true"
limiter = Limiter(key_func=get_remote_address, enabled=_RATE_LIMIT_ENABLED)

# ── Content-Security-Policy ──────────────────────────────────────────────────
_CSP = (
    "default-src 'self'; "
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "font-src https://cdn.jsdelivr.net data:; "
    "img-src 'self' data:; "
    "connect-src 'self'; "
    "form-action 'self'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """すべてのレスポンスにセキュリティヘッダーを付与する"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = _CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class CsrfMiddleware(BaseHTTPMiddleware):
    """
    CSRF 保護ミドルウェア（Origin / Referer ヘッダー検証）

    ブラウザが送信する POST リクエストには必ず Origin または Referer ヘッダーが付く。
    両ヘッダーが存在し、かつリクエストホストと一致しない場合はリジェクトする。
    ヘッダーが存在しない場合（curl やテストクライアント等）は許可する。
    """
    async def dispatch(self, request: Request, call_next):
        if request.method == "POST":
            host = request.headers.get("host", "")
            origin = request.headers.get("origin")
            referer = request.headers.get("referer")

            if origin is not None:
                # Origin ヘッダーがある場合: スキームとホストを除いた部分がリクエストホストと一致するか確認
                # e.g. "http://localhost:8000" → "localhost:8000"
                origin_host = origin.split("://", 1)[-1].rstrip("/")
                if origin_host != host:
                    logger.warning(
                        "[CSRF] Rejected POST from Origin=%r (expected host=%r) path=%s",
                        origin, host, request.url.path,
                    )
                    return JSONResponse(status_code=403, content={"detail": "CSRF protection: invalid origin"})
            elif referer is not None:
                # Referer ヘッダーのみある場合: Referer がホストを含むか確認
                if host not in referer:
                    logger.warning(
                        "[CSRF] Rejected POST from Referer=%r (expected host=%r) path=%s",
                        referer, host, request.url.path,
                    )
                    return JSONResponse(status_code=403, content={"detail": "CSRF protection: invalid referer"})

        return await call_next(request)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """アクセスログを出力する（リクエストID・IP・メソッド・パス・ステータス・レスポンスタイム）"""
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        # リクエストIDをリクエストのstateに保存（下流ハンドラーから参照可能）
        request.state.request_id = request_id

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        client_ip = request.client.host if request.client else "-"
        access_logger.info(
            "req_id=%s %s %s %s %d %.1fms",
            request_id,
            client_ip,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    Base.metadata.create_all(bind=engine)
    _migrate_emotional_scores_schema()
    _migrate_access_tokens()
    start_scheduler()
    yield
    # 終了時
    stop_scheduler()


def _migrate_emotional_scores_schema() -> None:
    """旧 emotional_scores スキーマ(5カラム)を新スキーマ(7カラム)へ移行する"""
    import sqlite3
    db_path = engine.url.database
    if not db_path:
        return
    conn = sqlite3.connect(db_path)
    try:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(emotional_scores)").fetchall()}
        if "anger_state_score" in cols:
            return
        if "anger_score" not in cols:
            return
        logger.info("[MIGRATE] Migrating emotional_scores schema from old to new columns")
        conn.execute("ALTER TABLE emotional_scores RENAME COLUMN anger_score TO anger_state_score")
        conn.execute("ALTER TABLE emotional_scores RENAME COLUMN regulation_score TO emotion_regulation_score")
        conn.execute("ALTER TABLE emotional_scores RENAME COLUMN mindfulness_score TO cognitive_pattern_score")
        conn.execute("ALTER TABLE emotional_scores RENAME COLUMN stress_score TO physiological_score")
        conn.execute("ALTER TABLE emotional_scores ADD COLUMN behavioral_score FLOAT NOT NULL DEFAULT 50.0")
        conn.execute("ALTER TABLE emotional_scores ADD COLUMN psychological_state_score FLOAT NOT NULL DEFAULT 50.0")
        conn.commit()
        logger.info("[MIGRATE] emotional_scores schema migration completed successfully")
    except Exception as e:
        logger.error("[MIGRATE] emotional_scores schema migration failed: %s", e)
        conn.rollback()
    finally:
        conn.close()


def _migrate_access_tokens() -> None:
    """既存セッションのうち access_token が NULL のものに UUID を付与する（一回限りの移行処理）"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        sessions_without_token = db.query(CheckInSession).filter(
            CheckInSession.access_token == None  # noqa: E711
        ).all()
        if not sessions_without_token:
            return
        for s in sessions_without_token:
            s.access_token = str(uuid.uuid4())
        db.commit()
        logger.info("[MIGRATE] Populated access_token for %d existing sessions", len(sessions_without_token))
    except Exception as e:
        logger.error("[MIGRATE] Failed to populate access_token: %s", e)
        db.rollback()
    finally:
        db.close()


app = FastAPI(
    title="たんちゃーならんど",
    lifespan=lifespan,
    docs_url="/docs" if _ENABLE_DOCS else None,
    redoc_url="/redoc" if _ENABLE_DOCS else None,
    openapi_url="/openapi.json" if _ENABLE_DOCS else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SecurityHeadersMiddleware)  # 内側（セキュリティヘッダー付与）
app.add_middleware(CsrfMiddleware)             # 中間（CSRF 保護）
app.add_middleware(AccessLogMiddleware)         # 外側（レスポンスタイム計測）
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

QUESTIONS_PER_SESSION = 10  # 1セッションあたりの出題数


# ─── ヘルスチェック ─── #
@app.get("/health")
async def health():
    """コンテナオーケストレーター向けヘルスチェックエンドポイント"""
    return {"status": "ok"}


# ─── ホーム画面 ─── #
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    sessions_today = (
        db.query(CheckInSession)
        .filter(func.date(CheckInSession.scheduled_at) == today)
        .order_by(CheckInSession.scheduled_at)
        .all()
    )
    completed_today = sum(1 for s in sessions_today if s.status == "completed")
    pending_session = next(
        (s for s in sessions_today if s.status == "pending" and s.scheduled_at <= datetime.now()),
        None,
    )
    next_session = next(
        (s for s in sessions_today if s.status == "pending" and s.scheduled_at > datetime.now()),
        None,
    )

    # 土日にセッションが0件の場合、振り返りプロンプトを表示
    is_weekend_prompt = (today.weekday() >= 5) and (len(sessions_today) == 0)

    # 直近スコア
    latest_score = (
        db.query(EmotionalScore)
        .order_by(EmotionalScore.id.desc())
        .first()
    )
    score_label, score_class = get_score_label(latest_score.overall_score) if latest_score else ("—", "secondary")
    message = get_random_message()

    return templates.TemplateResponse(request, "index.html", {
        "sessions_today": sessions_today,
        "completed_today": completed_today,
        "pending_session": pending_session,
        "next_session": next_session,
        "latest_score": latest_score,
        "score_label": score_label,
        "score_class": score_class,
        "message": message,
        "today": today,
        "is_weekend_prompt": is_weekend_prompt,
    })


# ─── チェックイン画面 ─── #
@app.get("/check-in", response_class=HTMLResponse)
async def check_in_page(request: Request, session_id: int | None = None, db: Session = Depends(get_db)):
    if session_id is not None:
        session = db.query(CheckInSession).filter(CheckInSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.status == "completed":
            token = session.access_token or str(session.id)
            return RedirectResponse(f"/check-in/result/{token}")
    else:
        # 新しいセッション（手動起動）
        session = CheckInSession(scheduled_at=datetime.now(), status="pending")
        db.add(session)
        db.commit()
        db.refresh(session)

    # セッションを開始状態に
    if session.status == "pending":
        session.status = "in_progress"
        session.started_at = datetime.now()
        db.commit()
        logger.info("[CHECK-IN] session_id=%d started", session.id)

    # 設問を選出: session.id をシードにすることで同一セッションでは再アクセス時も同じ問題を表示
    rng = random.Random(session.id)
    sampled = rng.sample(QUESTIONS, min(QUESTIONS_PER_SESSION, len(QUESTIONS)))
    message = get_random_message()

    return templates.TemplateResponse(request, "check_in.html", {
        "session": session,
        "questions": sampled,
        "message": message,
        "total": len(sampled),
    })


# ─── 回答送信 ─── #
@app.post("/check-in/submit", response_class=HTMLResponse)
@limiter.limit("60/minute")
async def submit_check_in(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    # session_id の型バリデーション
    try:
        session_id = int(form.get("session_id", ""))
        if session_id <= 0:
            raise ValueError
    except (ValueError, TypeError):
        logger.warning("[SUBMIT] Invalid session_id received: %r", form.get("session_id"))
        raise HTTPException(status_code=400, detail="Invalid session_id")

    session = db.query(CheckInSession).filter(CheckInSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 完了済みセッションへの再送信を拒否
    if session.status == "completed":
        logger.warning("[SUBMIT] Already completed session_id=%d", session_id)
        raise HTTPException(status_code=409, detail="Session already completed")

    # 回答を保存（question_id と answer_value を厳密に検証）
    answers = []
    for key, value in form.items():
        if not key.startswith("q_"):
            continue
        try:
            qid = int(key[2:])
            answer_value = int(value)
        except (ValueError, TypeError):
            logger.warning("[SUBMIT] Invalid form field session_id=%d key=%r value=%r", session_id, key, value)
            raise HTTPException(status_code=400, detail=f"Invalid field: {key}")

        # 設問IDがマスタに存在するか確認
        if qid not in QUESTION_BY_ID:
            logger.warning("[SUBMIT] Unknown question_id=%d session_id=%d", qid, session_id)
            raise HTTPException(status_code=400, detail=f"Unknown question_id: {qid}")

        # 回答値が 1〜4 の範囲内か確認
        if answer_value not in VALID_ANSWER_VALUES:
            logger.warning("[SUBMIT] Out-of-range answer_value=%d question_id=%d session_id=%d", answer_value, qid, session_id)
            raise HTTPException(status_code=400, detail=f"Invalid answer_value: {answer_value}")

        answers.append({"question_id": qid, "answer_value": answer_value})
        db.add(CheckInAnswer(
            session_id=session_id,
            question_id=qid,
            answer_value=answer_value,
            answered_at=datetime.now(),
        ))

    # スコアを計算・保存
    scores = calculate_scores(answers)
    emotional_score = EmotionalScore(
        session_id=session_id,
        date=date.today(),
        **scores,
    )
    db.add(emotional_score)

    # セッション完了
    session.status = "completed"
    session.completed_at = datetime.now()
    db.commit()

    logger.info(
        "[SUBMIT] session_id=%d completed answers=%d overall_score=%.1f",
        session_id,
        len(answers),
        scores.get("overall_score", 0.0),
    )
    token = session.access_token or str(session_id)
    return RedirectResponse(f"/check-in/result/{token}", status_code=303)


# ─── 結果画面 ─── #
@app.get("/check-in/result/{access_token}", response_class=HTMLResponse)
async def result_page(request: Request, access_token: str, db: Session = Depends(get_db)):
    session = db.query(CheckInSession).filter(CheckInSession.access_token == access_token).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    score = db.query(EmotionalScore).filter(EmotionalScore.session_id == session.id).first()
    answers = db.query(CheckInAnswer).filter(CheckInAnswer.session_id == session.id).all()

    # 高スコア設問のアドバイスを取得
    advices = []
    for ans in answers:
        q = QUESTION_BY_ID.get(ans.question_id)
        if not q:
            continue
        effective = (5 - ans.answer_value) if q["reverse"] else ans.answer_value
        if effective >= 3:  # スコアが高い（問題あり）項目
            advices.append({
                "question": q["text"],
                "explanation": q["explanation"],
                "advice": q["advice_high"],
            })

    score_label, score_class = get_score_label(score.overall_score) if score else ("—", "secondary")
    messages = get_messages(2)

    # 次のチェックイン
    next_session = (
        db.query(CheckInSession)
        .filter(CheckInSession.status == "pending", CheckInSession.scheduled_at > datetime.now())
        .order_by(CheckInSession.scheduled_at)
        .first()
    )

    response = templates.TemplateResponse(request, "result.html", {
        "session": session,
        "score": score,
        "score_label": score_label,
        "score_class": score_class,
        "advices": advices[:5],  # 最大5件
        "messages": messages,
        "next_session": next_session,
    })
    response.headers["Cache-Control"] = "no-store"
    return response


# ─── ダッシュボード ─── #
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "dashboard.html")


# ─── API: チェックイン状態確認（ポーリング用）─── #
@app.get("/api/status")
async def api_status(db: Session = Depends(get_db)):
    now = datetime.now()
    # 現在時刻の前後5分以内のpendingセッションを確認
    window_start = now - timedelta(minutes=5)
    pending = (
        db.query(CheckInSession)
        .filter(
            CheckInSession.status == "pending",
            CheckInSession.scheduled_at >= window_start,
            CheckInSession.scheduled_at <= now,
        )
        .order_by(CheckInSession.scheduled_at)
        .first()
    )
    if pending:
        return {"check_in_ready": True, "session_id": pending.id, "scheduled_at": pending.scheduled_at.isoformat()}
    return {"check_in_ready": False}


# ─── API: グラフ用データ ─── #
@app.get("/api/history")
async def api_history(days: int = Query(default=7, ge=1, le=365), db: Session = Depends(get_db)):
    since = date.today() - timedelta(days=days)
    scores = (
        db.query(EmotionalScore)
        .filter(EmotionalScore.date >= since)
        .order_by(EmotionalScore.date, EmotionalScore.id)
        .all()
    )

    # 日付ごとに集計
    daily: dict[str, list] = {}
    for s in scores:
        key = s.date.isoformat()
        if key not in daily:
            daily[key] = []
        daily[key].append(s)

    result = []
    for day_str, day_scores in sorted(daily.items()):
        result.append({
            "date": day_str,
            "overall": round(sum(s.overall_score for s in day_scores) / len(day_scores), 1),
            "anger_state": round(sum(s.anger_state_score for s in day_scores) / len(day_scores), 1),
            "cognitive_pattern": round(sum(s.cognitive_pattern_score for s in day_scores) / len(day_scores), 1),
            "physiological": round(sum(s.physiological_score for s in day_scores) / len(day_scores), 1),
            "behavioral": round(sum(s.behavioral_score for s in day_scores) / len(day_scores), 1),
            "emotion_regulation": round(sum(s.emotion_regulation_score for s in day_scores) / len(day_scores), 1),
            "psychological_state": round(sum(s.psychological_state_score for s in day_scores) / len(day_scores), 1),
            "sessions": len(day_scores),
        })
    return result


# ─── API: 土日振り返りセッション生成 ─── #
@app.post("/api/sessions/weekend")
@limiter.limit("10/minute")
async def api_create_weekend_session(request: Request, db: Session = Depends(get_db)):
    """土日限定: 振り返り用チェックインセッションを 18:00〜21:00 の間に1件生成する"""
    today = date.today()
    if today.weekday() < 5:
        raise HTTPException(status_code=400, detail="Today is not a weekend")

    existing = (
        db.query(CheckInSession)
        .filter(func.date(CheckInSession.scheduled_at) == today)
        .count()
    )
    if existing >= 1:
        raise HTTPException(status_code=409, detail="Weekend session already exists for today")

    m = random.randint(1080, 1259)  # 18:00〜20:59
    scheduled = datetime(today.year, today.month, today.day, m // 60, m % 60)
    session = CheckInSession(scheduled_at=scheduled, status="pending")
    db.add(session)
    db.commit()
    db.refresh(session)
    logger.info("[WEEKEND] Created weekend session at %s", scheduled.strftime("%H:%M"))
    return {"session_id": session.id, "scheduled_at": scheduled.isoformat()}


# ─── API: セッション一覧 ─── #
@app.get("/api/sessions")
async def api_sessions(limit: int = Query(default=20, ge=1, le=200), db: Session = Depends(get_db)):
    sessions = (
        db.query(CheckInSession)
        .order_by(CheckInSession.scheduled_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for s in sessions:
        item = {
            "id": s.id,
            "scheduled_at": s.scheduled_at.isoformat(),
            "status": s.status,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
        }
        if s.score:
            item["overall_score"] = s.score.overall_score
        result.append(item)
    return result
