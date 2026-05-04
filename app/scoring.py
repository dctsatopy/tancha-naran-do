from app.questions_data import QUESTION_BY_ID

# 重み付け定数（仕様 §4.1）
# 根拠: Novaco (1994), InAn (2025), STAXI-2, CAS, K6, DASS-21
CATEGORY_WEIGHTS = {
    "anger_state": 0.25,
    "cognitive_pattern": 0.20,
    "physiological": 0.15,
    "behavioral": 0.15,
    "emotion_regulation": 0.15,
    "psychological_state": 0.10,
}


def calculate_scores(answers: list[dict]) -> dict:
    """
    answers: [{"question_id": int, "answer_value": int}, ...]
    returns: 6カテゴリスコア + overall_score
    """
    category_scores = {cat: [] for cat in CATEGORY_WEIGHTS}

    for ans in answers:
        qid = ans["question_id"]
        value = ans["answer_value"]
        q = QUESTION_BY_ID.get(qid)
        if not q:
            continue
        score = (5 - value) if q["reverse"] else value
        cat = q["category"]
        if cat in category_scores:
            category_scores[cat].append(score)

    def avg(lst):
        return sum(lst) / len(lst) if lst else 2.5

    raw = {cat: avg(category_scores[cat]) for cat in CATEGORY_WEIGHTS}

    normalized = {}
    for cat, raw_val in raw.items():
        normalized[cat] = round((raw_val - 1) / 3 * 100, 1)

    overall = round(
        sum(
            (100 - normalized[cat]) * weight
            for cat, weight in CATEGORY_WEIGHTS.items()
        ),
        1,
    )

    return {
        "anger_state_score": normalized["anger_state"],
        "cognitive_pattern_score": normalized["cognitive_pattern"],
        "physiological_score": normalized["physiological"],
        "behavioral_score": normalized["behavioral"],
        "emotion_regulation_score": normalized["emotion_regulation"],
        "psychological_state_score": normalized["psychological_state"],
        "overall_score": min(100.0, max(0.0, overall)),
    }


def get_score_label(overall_score: float) -> tuple[str, str]:
    """overall_score から状態ラベルと色クラスを返す

    閾値根拠:
    - ≥70: CAS minimal ≈ 79%, K6 low ≈ 79%, DASS-21 normal ≈ 67% の収束点
    - ≥45: K6 moderate ≈ 46%, DASS-21 moderate ≈ 41% の中間域
    - ≥25: DASS-21 severe ≈ 21% 付近
    - <25: 複数尺度で臨床的に有意な水準
    """
    if overall_score >= 70:
        return "良好", "success"
    elif overall_score >= 45:
        return "普通", "warning"
    elif overall_score >= 25:
        return "注意", "danger"
    else:
        return "要ケア", "dark"
