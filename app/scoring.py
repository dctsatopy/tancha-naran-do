from app.questions_data import QUESTION_BY_ID


def calculate_scores(answers: list[dict]) -> dict:
    """
    answers: [{"question_id": int, "answer_value": int}, ...]
    returns: {"anger": float, "regulation": float, "mindfulness": float, "stress": float, "overall": float}
    """
    category_scores = {"anger": [], "regulation": [], "cognitive_regulation": [], "mindfulness": [], "stress": []}

    for ans in answers:
        qid = ans["question_id"]
        value = ans["answer_value"]
        q = QUESTION_BY_ID.get(qid)
        if not q:
            continue
        # 逆転項目は 5 - value でスコア変換 (1-4 スケール)
        score = (5 - value) if q["reverse"] else value
        cat = q["category"]
        if cat in category_scores:
            category_scores[cat].append(score)

    def avg(lst):
        return sum(lst) / len(lst) if lst else 2.5

    anger_raw = avg(category_scores["anger"])          # 高い = 怒り強い (bad)
    regulation_raw = avg(category_scores["regulation"])  # 高い = 調節困難 or 良好（混在）
    cognitive_raw = avg(category_scores["cognitive_regulation"])
    mindfulness_raw = avg(category_scores["mindfulness"])
    stress_raw = avg(category_scores["stress"])

    # 正規化: anger/stress は「低いほど良い」→ 反転して100点スケールに
    # regulation/cognitive/mindfulness は「高いほど良い」→ そのまま100点スケールに
    anger_score = round((anger_raw - 1) / 3 * 100, 1)          # 0-100 (高い = 怒り強い)
    regulation_score = round((regulation_raw - 1) / 3 * 100, 1)  # 0-100 (高い = 困難 or 良好)
    mindfulness_score = round((mindfulness_raw - 1) / 3 * 100, 1)
    stress_score = round((stress_raw - 1) / 3 * 100, 1)

    # overall = 怒りとストレスを反転して合算
    overall = round(
        (
            (100 - anger_score) * 0.3
            + regulation_score * 0.2
            + (100 - stress_score) * 0.2
            + mindfulness_score * 0.2
            + (100 - stress_score) * 0.1
        ),
        1,
    )

    return {
        "anger_score": anger_score,
        "regulation_score": regulation_score,
        "mindfulness_score": mindfulness_score,
        "stress_score": stress_score,
        "overall_score": min(100.0, max(0.0, overall)),
    }


def get_score_label(overall_score: float) -> tuple[str, str]:
    """overall_score から状態ラベルと色クラスを返す"""
    if overall_score >= 75:
        return "良好", "success"
    elif overall_score >= 50:
        return "普通", "warning"
    elif overall_score >= 25:
        return "注意", "danger"
    else:
        return "要ケア", "dark"
