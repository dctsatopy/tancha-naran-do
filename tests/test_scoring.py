"""
スコア計算ロジック (app/scoring.py) のユニットテスト

仕様参照: development_background.md §4.1
スコアリング根拠: CAS (Snell 1995), K6 (Kessler 2003), DASS-21, NAS (Novaco 1994), InAn (2025)
"""
import pytest
from app.scoring import calculate_scores, get_score_label
from app.questions_data import QUESTIONS, QUESTION_BY_ID

# 新カテゴリ一覧
NEW_CATEGORIES = [
    "anger_state", "cognitive_pattern", "physiological",
    "behavioral", "emotion_regulation", "psychological_state",
]

# 期待されるスコアキー
EXPECTED_SCORE_KEYS = {
    "anger_state_score", "cognitive_pattern_score", "physiological_score",
    "behavioral_score", "emotion_regulation_score", "psychological_state_score",
    "overall_score",
}

# 重み付け定数（仕様 §4.1）
WEIGHTS = {
    "anger_state": 0.25,
    "cognitive_pattern": 0.20,
    "physiological": 0.15,
    "behavioral": 0.15,
    "emotion_regulation": 0.15,
    "psychological_state": 0.10,
}


class TestCalculateScores:
    """calculate_scores() の入出力検証"""

    def _answers_for_category(self, category: str, value: int) -> list[dict]:
        """指定カテゴリの全設問に同じ値で回答するリストを返す"""
        return [
            {"question_id": q["id"], "answer_value": value}
            for q in QUESTIONS if q["category"] == category
        ]

    def test_returns_all_score_keys(self):
        """必要な7つのスコアキーがすべて返ること"""
        scores = calculate_scores([])
        assert EXPECTED_SCORE_KEYS == set(scores.keys())

    def test_all_scores_in_range_0_to_100(self):
        """全スコアが 0〜100 の範囲内であること"""
        for value in [1, 2, 3, 4]:
            answers = [{"question_id": q["id"], "answer_value": value} for q in QUESTIONS]
            scores = calculate_scores(answers)
            for key, val in scores.items():
                assert 0.0 <= val <= 100.0, f"value={value} {key}={val} is out of range"

    def test_overall_score_clamped(self):
        """overall_score は必ず 0〜100 にクランプされること"""
        answers = [{"question_id": q["id"], "answer_value": 4} for q in QUESTIONS]
        scores = calculate_scores(answers)
        assert 0.0 <= scores["overall_score"] <= 100.0

    def test_empty_answers_returns_defaults(self):
        """回答が空のときデフォルト値（2.5 基準）でスコアが返ること"""
        scores = calculate_scores([])
        assert scores["anger_state_score"] == pytest.approx(50.0, abs=0.1)
        assert 0.0 <= scores["overall_score"] <= 100.0

    def test_anger_state_score_max_with_non_reverse_all_4(self):
        """非逆転の怒り状態設問に 4 を回答すると anger_state_score が 100 になること"""
        answers = [
            {"question_id": q["id"], "answer_value": 4}
            for q in QUESTIONS if q["category"] == "anger_state" and not q["reverse"]
        ]
        scores = calculate_scores(answers)
        assert scores["anger_state_score"] == pytest.approx(100.0, abs=0.1)

    def test_anger_state_score_min_with_non_reverse_all_1(self):
        """非逆転の怒り状態設問に 1 を回答すると anger_state_score が 0 になること"""
        answers = [
            {"question_id": q["id"], "answer_value": 1}
            for q in QUESTIONS if q["category"] == "anger_state" and not q["reverse"]
        ]
        scores = calculate_scores(answers)
        assert scores["anger_state_score"] == pytest.approx(0.0, abs=0.1)

    def test_reverse_item_inversion(self):
        """逆転項目は (5 - value) でスコアが計算されること"""
        reverse_q = next(q for q in QUESTIONS if q["reverse"] and q["category"] == "emotion_regulation")
        normal_q = next(q for q in QUESTIONS if not q["reverse"] and q["category"] == "emotion_regulation")

        answers_reverse_high = [{"question_id": reverse_q["id"], "answer_value": 4}]
        answers_normal_high = [{"question_id": normal_q["id"], "answer_value": 4}]

        score_reverse = calculate_scores(answers_reverse_high)["emotion_regulation_score"]
        score_normal = calculate_scores(answers_normal_high)["emotion_regulation_score"]
        assert score_reverse < score_normal, "逆転項目は通常項目より低スコアになること"

    def test_unknown_question_id_is_ignored(self):
        """存在しない question_id は無視されてもスコア計算が正常に完了すること"""
        answers = [{"question_id": 9999, "answer_value": 4}]
        scores = calculate_scores(answers)
        assert "overall_score" in scores

    def test_score_monotonicity_anger_state(self):
        """怒り状態カテゴリへの回答値が大きいほど anger_state_score が高くなること"""
        scores_by_value = {}
        for v in [1, 2, 3, 4]:
            ans = [{"question_id": q["id"], "answer_value": v}
                   for q in QUESTIONS if q["category"] == "anger_state" and not q["reverse"]]
            scores_by_value[v] = calculate_scores(ans)["anger_state_score"]

        assert scores_by_value[1] < scores_by_value[2] < scores_by_value[3] < scores_by_value[4]

    def test_score_monotonicity_cognitive_pattern(self):
        """認知パターンへの回答値が大きいほど cognitive_pattern_score が高くなること"""
        scores_by_value = {}
        for v in [1, 2, 3, 4]:
            ans = [{"question_id": q["id"], "answer_value": v}
                   for q in QUESTIONS if q["category"] == "cognitive_pattern" and not q["reverse"]]
            scores_by_value[v] = calculate_scores(ans)["cognitive_pattern_score"]

        assert scores_by_value[1] < scores_by_value[2] < scores_by_value[3] < scores_by_value[4]

    def test_overall_decreases_when_anger_state_is_high(self):
        """怒り状態スコアが高いほど overall が下がること"""
        non_reverse = [q for q in QUESTIONS if q["category"] == "anger_state" and not q["reverse"]]
        scores_low = calculate_scores([{"question_id": q["id"], "answer_value": 1} for q in non_reverse])
        scores_high = calculate_scores([{"question_id": q["id"], "answer_value": 4} for q in non_reverse])
        assert scores_low["overall_score"] > scores_high["overall_score"]

    def test_overall_decreases_when_cognitive_distortion_is_high(self):
        """認知的歪みが高いほど overall が下がること"""
        non_reverse = [q for q in QUESTIONS if q["category"] == "cognitive_pattern" and not q["reverse"]]
        scores_low = calculate_scores([{"question_id": q["id"], "answer_value": 1} for q in non_reverse])
        scores_high = calculate_scores([{"question_id": q["id"], "answer_value": 4} for q in non_reverse])
        assert scores_low["overall_score"] > scores_high["overall_score"]

    def test_score_precision(self):
        """スコアは小数点1位で返ること"""
        answers = [{"question_id": 1, "answer_value": 3}]
        scores = calculate_scores(answers)
        for val in scores.values():
            assert round(val, 1) == val

    def test_all_answers_value_2_yields_midpoint_scores(self):
        """全設問に 2 を回答した場合、各カテゴリスコアが 0〜100 の範囲内であること"""
        answers = [{"question_id": q["id"], "answer_value": 2} for q in QUESTIONS]
        scores = calculate_scores(answers)
        for key, val in scores.items():
            assert 0.0 <= val <= 100.0, f"{key}={val} が範囲外"

    def test_single_answer_per_category_returns_valid_scores(self):
        """各カテゴリから1問だけ回答した場合でも有効なスコアが返ること"""
        for cat in NEW_CATEGORIES:
            q = next(q for q in QUESTIONS if q["category"] == cat)
            answers = [{"question_id": q["id"], "answer_value": 1}]
            scores = calculate_scores(answers)
            for key, val in scores.items():
                assert 0.0 <= val <= 100.0, f"category={cat} {key}={val} が範囲外"

    def test_all_scores_boundary_value_1(self):
        """全設問に最小値 1 を回答した場合すべてのスコアが 0〜100 の範囲内であること"""
        answers = [{"question_id": q["id"], "answer_value": 1} for q in QUESTIONS]
        scores = calculate_scores(answers)
        for key, val in scores.items():
            assert 0.0 <= val <= 100.0, f"answer=1 {key}={val} が範囲外"

    def test_all_scores_boundary_value_4(self):
        """全設問に最大値 4 を回答した場合すべてのスコアが 0〜100 の範囲内であること"""
        answers = [{"question_id": q["id"], "answer_value": 4} for q in QUESTIONS]
        scores = calculate_scores(answers)
        for key, val in scores.items():
            assert 0.0 <= val <= 100.0, f"answer=4 {key}={val} が範囲外"

    def test_weights_sum_to_1(self):
        """重み付けの合計が 1.0 であること（仕様 §4.1）"""
        assert sum(WEIGHTS.values()) == pytest.approx(1.0)

    def test_overall_perfect_when_all_non_reverse_answer_1(self):
        """全非逆転項目に1、全逆転項目に4を回答した場合 overall が100に近いこと"""
        answers = []
        for q in QUESTIONS:
            if q["reverse"]:
                answers.append({"question_id": q["id"], "answer_value": 4})
            else:
                answers.append({"question_id": q["id"], "answer_value": 1})
        scores = calculate_scores(answers)
        assert scores["overall_score"] == pytest.approx(100.0, abs=0.1)

    def test_overall_worst_when_all_non_reverse_answer_4(self):
        """全非逆転項目に4、全逆転項目に1を回答した場合 overall が0に近いこと"""
        answers = []
        for q in QUESTIONS:
            if q["reverse"]:
                answers.append({"question_id": q["id"], "answer_value": 1})
            else:
                answers.append({"question_id": q["id"], "answer_value": 4})
        scores = calculate_scores(answers)
        assert scores["overall_score"] == pytest.approx(0.0, abs=0.1)

    def test_each_category_independently_affects_overall(self):
        """各カテゴリのスコア変化が overall に独立して影響すること"""
        base_scores = calculate_scores([])
        for cat in NEW_CATEGORIES:
            non_reverse = [q for q in QUESTIONS if q["category"] == cat and not q["reverse"]]
            if not non_reverse:
                continue
            high_answers = [{"question_id": q["id"], "answer_value": 4} for q in non_reverse]
            cat_scores = calculate_scores(high_answers)
            assert cat_scores["overall_score"] < base_scores["overall_score"], (
                f"カテゴリ '{cat}' の高スコアが overall を下げるべき"
            )


class TestGetScoreLabel:
    """get_score_label() の境界値テスト（CAS・K6・DASS-21 に基づく閾値）"""

    @pytest.mark.parametrize("score,expected_label,expected_class", [
        (100.0, "良好", "success"),
        (70.0, "良好", "success"),
        (69.9, "普通", "warning"),
        (45.0, "普通", "warning"),
        (44.9, "注意", "danger"),
        (25.0, "注意", "danger"),
        (24.9, "要ケア", "dark"),
        (0.0, "要ケア", "dark"),
    ])
    def test_score_label_boundary(self, score, expected_label, expected_class):
        label, css_class = get_score_label(score)
        assert label == expected_label, f"score={score}: expected '{expected_label}', got '{label}'"
        assert css_class == expected_class, f"score={score}: expected '{expected_class}', got '{css_class}'"
