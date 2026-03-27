"""
スコア計算ロジック (app/scoring.py) のユニットテスト

仕様参照: tancha_naran_do.md §3.1, §7
"""
import pytest
from app.scoring import calculate_scores, get_score_label
from app.questions_data import QUESTIONS, QUESTION_BY_ID


class TestCalculateScores:
    """calculate_scores() の入出力検証"""

    def _answers_for_category(self, category: str, value: int) -> list[dict]:
        """指定カテゴリの全設問に同じ値で回答するリストを返す"""
        return [
            {"question_id": q["id"], "answer_value": value}
            for q in QUESTIONS if q["category"] == category
        ]

    def test_returns_all_score_keys(self):
        """必要な5つのスコアキーがすべて返ること"""
        scores = calculate_scores([])
        expected_keys = {
            "anger_score", "regulation_score", "mindfulness_score",
            "stress_score", "overall_score",
        }
        assert expected_keys == set(scores.keys())

    def test_all_scores_in_range_0_to_100(self):
        """全スコアが 0〜100 の範囲内であること"""
        for value in [1, 2, 3, 4]:
            answers = [{"question_id": q["id"], "answer_value": value} for q in QUESTIONS]
            scores = calculate_scores(answers)
            for key, val in scores.items():
                assert 0.0 <= val <= 100.0, f"value={value} {key}={val} is out of range"

    def test_overall_score_clamped(self):
        """overall_score は必ず 0〜100 にクランプされること"""
        # 最高怒りスコア
        answers = [{"question_id": q["id"], "answer_value": 4} for q in QUESTIONS]
        scores = calculate_scores(answers)
        assert 0.0 <= scores["overall_score"] <= 100.0

    def test_empty_answers_returns_defaults(self):
        """回答が空のときデフォルト値（2.5 基準）でスコアが返ること"""
        scores = calculate_scores([])
        # 2.5 基準なので anger_score = (2.5-1)/3*100 ≈ 50.0
        assert scores["anger_score"] == pytest.approx(50.0, abs=0.1)
        assert 0.0 <= scores["overall_score"] <= 100.0

    def test_anger_score_max_with_non_reverse_all_4(self):
        """非逆転の怒り設問のみに 4 を回答すると anger_score が 100 になること"""
        # 非逆転: score = value → 4 → anger_raw = 4 → (4-1)/3*100 = 100
        answers = [
            {"question_id": q["id"], "answer_value": 4}
            for q in QUESTIONS if q["category"] == "anger" and not q["reverse"]
        ]
        scores = calculate_scores(answers)
        assert scores["anger_score"] == pytest.approx(100.0, abs=0.1)

    def test_anger_score_min_with_non_reverse_all_1(self):
        """非逆転の怒り設問のみに 1 を回答すると anger_score が 0 になること"""
        # 非逆転: score = value → 1 → anger_raw = 1 → (1-1)/3*100 = 0
        answers = [
            {"question_id": q["id"], "answer_value": 1}
            for q in QUESTIONS if q["category"] == "anger" and not q["reverse"]
        ]
        scores = calculate_scores(answers)
        assert scores["anger_score"] == pytest.approx(0.0, abs=0.1)

    def test_anger_score_with_mixed_reverse(self):
        """全怒り設問（逆転含む）に 4 を回答した場合のスコアが期待値であること"""
        # 怒り: 非逆転 33問 × スコア4 + 逆転 17問 × スコア1 = 149
        # anger_raw = 149/50 = 2.98
        # anger_score = (2.98-1)/3*100 ≈ 66.0
        answers = self._answers_for_category("anger", 4)
        scores = calculate_scores(answers)
        assert scores["anger_score"] == pytest.approx(66.0, abs=0.5)

    def test_reverse_item_inversion(self):
        """逆転項目は (5 - value) でスコアが計算されること"""
        reverse_q = next(q for q in QUESTIONS if q["reverse"] and q["category"] == "mindfulness")
        normal_q = next(q for q in QUESTIONS if not q["reverse"] and q["category"] == "mindfulness")

        # 逆転項目に 4 → 実効値 1 → 低スコア
        answers_reverse_high = [{"question_id": reverse_q["id"], "answer_value": 4}]
        # 通常項目に 4 → 実効値 4 → 高スコア
        answers_normal_high = [{"question_id": normal_q["id"], "answer_value": 4}]

        score_reverse = calculate_scores(answers_reverse_high)["mindfulness_score"]
        score_normal = calculate_scores(answers_normal_high)["mindfulness_score"]
        assert score_reverse < score_normal, "逆転項目は通常項目より低スコアになること"

    def test_unknown_question_id_is_ignored(self):
        """存在しない question_id は無視されてもスコア計算が正常に完了すること"""
        answers = [{"question_id": 9999, "answer_value": 4}]
        scores = calculate_scores(answers)
        assert "overall_score" in scores

    def test_score_monotonicity_anger(self):
        """怒りカテゴリへの回答値が大きいほど anger_score が高くなること"""
        scores_by_value = {}
        for v in [1, 2, 3, 4]:
            ans = [{"question_id": q["id"], "answer_value": v}
                   for q in QUESTIONS if q["category"] == "anger" and not q["reverse"]]
            scores_by_value[v] = calculate_scores(ans)["anger_score"]

        assert scores_by_value[1] < scores_by_value[2] < scores_by_value[3] < scores_by_value[4]

    def test_score_precision(self):
        """スコアは小数点1位で返ること"""
        answers = [{"question_id": 1, "answer_value": 3}]
        scores = calculate_scores(answers)
        for val in scores.values():
            # 小数点1桁以内（round(x, 1) と一致）
            assert round(val, 1) == val


class TestGetScoreLabel:
    """get_score_label() の境界値テスト"""

    @pytest.mark.parametrize("score,expected_label,expected_class", [
        (100.0, "良好", "success"),
        (75.0, "良好", "success"),
        (74.9, "普通", "warning"),
        (50.0, "普通", "warning"),
        (49.9, "注意", "danger"),
        (25.0, "注意", "danger"),
        (24.9, "要ケア", "dark"),
        (0.0, "要ケア", "dark"),
    ])
    def test_score_label_boundary(self, score, expected_label, expected_class):
        label, css_class = get_score_label(score)
        assert label == expected_label, f"score={score}: expected '{expected_label}', got '{label}'"
        assert css_class == expected_class, f"score={score}: expected '{expected_class}', got '{css_class}'"
