import random
import logging
from datetime import datetime, date, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import engine, get_db
from app.models import Base, CheckInSession, CheckInAnswer, EmotionalScore
from app.questions_data import QUESTIONS, QUESTION_BY_ID
from app.messages_data import get_random_message, get_messages
from app.scoring import calculate_scores, get_score_label
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 起動時
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    # 終了時
    stop_scheduler()


app = FastAPI(title="たんちゃーならんど", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

QUESTIONS_PER_SESSION = 10  # 1セッションあたりの出題数


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

    # 直近スコア
    latest_score = (
        db.query(EmotionalScore)
        .order_by(EmotionalScore.id.desc())
        .first()
    )
    score_label, score_class = get_score_label(latest_score.overall_score) if latest_score else ("—", "secondary")
    message = get_random_message()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "sessions_today": sessions_today,
        "completed_today": completed_today,
        "pending_session": pending_session,
        "next_session": next_session,
        "latest_score": latest_score,
        "score_label": score_label,
        "score_class": score_class,
        "message": message,
        "today": today,
    })


# ─── チェックイン画面 ─── #
@app.get("/check-in", response_class=HTMLResponse)
async def check_in_page(request: Request, session_id: int | None = None, db: Session = Depends(get_db)):
    if session_id:
        session = db.query(CheckInSession).filter(CheckInSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        if session.status == "completed":
            return RedirectResponse(f"/check-in/result/{session_id}")
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

    # ランダムに設問を選出（カテゴリバランスを考慮）
    sampled = random.sample(QUESTIONS, min(QUESTIONS_PER_SESSION, len(QUESTIONS)))
    message = get_random_message()

    return templates.TemplateResponse("check_in.html", {
        "request": request,
        "session": session,
        "questions": sampled,
        "message": message,
        "total": len(sampled),
    })


# ─── 回答送信 ─── #
@app.post("/check-in/submit", response_class=HTMLResponse)
async def submit_check_in(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    session_id = int(form.get("session_id", 0))

    session = db.query(CheckInSession).filter(CheckInSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 回答を保存
    answers = []
    for key, value in form.items():
        if key.startswith("q_"):
            qid = int(key[2:])
            answers.append({"question_id": qid, "answer_value": int(value)})
            db.add(CheckInAnswer(
                session_id=session_id,
                question_id=qid,
                answer_value=int(value),
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

    return RedirectResponse(f"/check-in/result/{session_id}", status_code=303)


# ─── 結果画面 ─── #
@app.get("/check-in/result/{session_id}", response_class=HTMLResponse)
async def result_page(request: Request, session_id: int, db: Session = Depends(get_db)):
    session = db.query(CheckInSession).filter(CheckInSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    score = db.query(EmotionalScore).filter(EmotionalScore.session_id == session_id).first()
    answers = db.query(CheckInAnswer).filter(CheckInAnswer.session_id == session_id).all()

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

    return templates.TemplateResponse("result.html", {
        "request": request,
        "session": session,
        "score": score,
        "score_label": score_label,
        "score_class": score_class,
        "advices": advices[:5],  # 最大5件
        "messages": messages,
        "next_session": next_session,
    })


# ─── ダッシュボード ─── #
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("dashboard.html", {"request": request})


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
async def api_history(days: int = 7, db: Session = Depends(get_db)):
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
            "anger": round(sum(s.anger_score for s in day_scores) / len(day_scores), 1),
            "regulation": round(sum(s.regulation_score for s in day_scores) / len(day_scores), 1),
            "mindfulness": round(sum(s.mindfulness_score for s in day_scores) / len(day_scores), 1),
            "stress": round(sum(s.stress_score for s in day_scores) / len(day_scores), 1),
            "sessions": len(day_scores),
        })
    return result


# ─── API: セッション一覧 ─── #
@app.get("/api/sessions")
async def api_sessions(limit: int = 20, db: Session = Depends(get_db)):
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
