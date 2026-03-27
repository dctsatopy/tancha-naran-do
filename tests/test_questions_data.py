"""
設問データ (app/questions_data.py) のユニットテスト

仕様参照: tancha_naran_do.md §3.1, §4
"""
import pytest
from app.questions_data import QUESTIONS, QUESTION_BY_ID, CATEGORY_IDS


class TestQuestionsData:
    """QUESTIONS リストの構造・内容を検証する"""

    def test_total_question_count(self):
        """設問総数が 200 問であること（仕様 §3.1）"""
        assert len(QUESTIONS) == 200

    def test_unique_question_ids(self):
        """設問 ID に重複がないこと"""
        ids = [q["id"] for q in QUESTIONS]
        assert len(set(ids)) == len(ids), "設問 ID に重複があります"

    def test_sequential_question_ids_1_to_200(self):
        """設問 ID が 1〜200 の連番であること"""
        ids = sorted(q["id"] for q in QUESTIONS)
        assert ids == list(range(1, 201))

    @pytest.mark.parametrize("field", ["id", "category", "text", "reverse", "explanation", "advice_high", "advice_low"])
    def test_required_fields_present(self, field):
        """各設問に必須フィールドが揃っていること"""
        missing = [q["id"] for q in QUESTIONS if field not in q]
        assert not missing, f"フィールド '{field}' が欠損している設問 ID: {missing}"

    def test_reverse_field_is_bool(self):
        """reverse フィールドが bool 型であること"""
        non_bool = [q["id"] for q in QUESTIONS if not isinstance(q["reverse"], bool)]
        assert not non_bool, f"reverse が bool でない設問 ID: {non_bool}"

    def test_valid_categories(self):
        """category フィールドが定義済みカテゴリのいずれかであること"""
        valid = {"anger", "regulation", "cognitive_regulation", "mindfulness", "stress"}
        invalid = [q["id"] for q in QUESTIONS if q["category"] not in valid]
        assert not invalid, f"不正な category の設問 ID: {invalid}"

    def test_text_not_empty(self):
        """全設問の text が空でないこと"""
        empty = [q["id"] for q in QUESTIONS if not q["text"].strip()]
        assert not empty, f"text が空の設問 ID: {empty}"

    def test_category_anger_count(self):
        """怒りカテゴリが 50 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["anger"]) == 50

    def test_category_regulation_count(self):
        """感情調節困難カテゴリが 40 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["regulation"]) == 40

    def test_category_mindfulness_count(self):
        """マインドフルネスカテゴリが 34 問であること"""
        assert len(CATEGORY_IDS["mindfulness"]) == 34

    def test_category_stress_count(self):
        """ストレスカテゴリが 40 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["stress"]) == 40

    def test_category_cognitive_regulation_count(self):
        """認知的感情調節カテゴリが 36 問であること"""
        assert len(CATEGORY_IDS["cognitive_regulation"]) == 36

    def test_total_by_category(self):
        """カテゴリ別合計が 200 問になること"""
        total = sum(len(v) for v in CATEGORY_IDS.values())
        assert total == 200

    def test_reverse_question_counts(self):
        """逆転項目が 114 問、非逆転が 86 問であること"""
        reverse_count = sum(1 for q in QUESTIONS if q["reverse"])
        normal_count = sum(1 for q in QUESTIONS if not q["reverse"])
        assert reverse_count == 114
        assert normal_count == 86


class TestQuestionById:
    """QUESTION_BY_ID 辞書の検証"""

    def test_all_questions_indexed(self):
        """QUESTION_BY_ID に全 200 問がインデックスされていること"""
        assert len(QUESTION_BY_ID) == 200

    def test_lookup_by_id(self):
        """任意の ID で設問が取得できること"""
        for qid in [1, 100, 200]:
            q = QUESTION_BY_ID.get(qid)
            assert q is not None, f"question_id={qid} が見つかりません"
            assert q["id"] == qid

    def test_unknown_id_returns_none(self):
        """存在しない ID は None を返すこと"""
        assert QUESTION_BY_ID.get(0) is None
        assert QUESTION_BY_ID.get(201) is None
        assert QUESTION_BY_ID.get(9999) is None

    def test_reference_same_object(self):
        """QUESTION_BY_ID の値は QUESTIONS リストと同一オブジェクトであること"""
        for q in QUESTIONS:
            assert QUESTION_BY_ID[q["id"]] is q
