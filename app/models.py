import uuid
from datetime import datetime, date
from sqlalchemy import Integer, Float, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CheckInSession(Base):
    __tablename__ = "check_in_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    access_token: Mapped[str | None] = mapped_column(
        String(36), unique=True, index=True, nullable=True, default=lambda: str(uuid.uuid4())
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending/in_progress/completed/skipped

    answers: Mapped[list["CheckInAnswer"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    score: Mapped["EmotionalScore | None"] = relationship(back_populates="session", uselist=False)


class CheckInAnswer(Base):
    __tablename__ = "check_in_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("check_in_sessions.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_value: Mapped[int] = mapped_column(Integer, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    session: Mapped["CheckInSession"] = relationship(back_populates="answers")


class EmotionalScore(Base):
    __tablename__ = "emotional_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("check_in_sessions.id"), nullable=False, unique=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    anger_score: Mapped[float] = mapped_column(Float, nullable=False)
    regulation_score: Mapped[float] = mapped_column(Float, nullable=False)
    mindfulness_score: Mapped[float] = mapped_column(Float, nullable=False)
    stress_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)

    session: Mapped["CheckInSession"] = relationship(back_populates="score")
