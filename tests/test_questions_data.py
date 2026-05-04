"""
設問データ (app/questions_data.py) のユニットテスト

仕様参照: development_background.md §3.1, §4
"""
import pytest
from app.questions_data import QUESTIONS, QUESTION_BY_ID, CATEGORY_IDS


class TestQuestionsData:
    """QUESTIONS リストの構造・内容を検証する"""

    def test_total_question_count(self):
        """設問総数が 120 問であること（仕様 §3.1）"""
        assert len(QUESTIONS) == 120

    def test_unique_question_ids(self):
        """設問 ID に重複がないこと"""
        ids = [q["id"] for q in QUESTIONS]
        assert len(set(ids)) == len(ids), "設問 ID に重複があります"

    def test_sequential_question_ids_1_to_120(self):
        """設問 ID が 1〜120 の連番であること"""
        ids = sorted(q["id"] for q in QUESTIONS)
        assert ids == list(range(1, 121))

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
        """category フィールドが定義済み6カテゴリのいずれかであること"""
        valid = {"anger_state", "cognitive_pattern", "physiological", "behavioral", "emotion_regulation", "psychological_state"}
        invalid = [q["id"] for q in QUESTIONS if q["category"] not in valid]
        assert not invalid, f"不正な category の設問 ID: {invalid}"

    def test_text_not_empty(self):
        """全設問の text が空でないこと"""
        empty = [q["id"] for q in QUESTIONS if not q["text"].strip()]
        assert not empty, f"text が空の設問 ID: {empty}"

    def test_category_anger_state_count(self):
        """怒りの状態カテゴリが 25 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["anger_state"]) == 25

    def test_category_cognitive_pattern_count(self):
        """認知パターンカテゴリが 25 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["cognitive_pattern"]) == 25

    def test_category_physiological_count(self):
        """身体反応カテゴリが 15 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["physiological"]) == 15

    def test_category_behavioral_count(self):
        """行動傾向カテゴリが 20 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["behavioral"]) == 20

    def test_category_emotion_regulation_count(self):
        """感情調節カテゴリが 20 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["emotion_regulation"]) == 20

    def test_category_psychological_state_count(self):
        """心理的状態カテゴリが 15 問であること（仕様 §4）"""
        assert len(CATEGORY_IDS["psychological_state"]) == 15

    def test_total_by_category(self):
        """カテゴリ別合計が 120 問になること"""
        total = sum(len(v) for v in CATEGORY_IDS.values())
        assert total == 120

    def test_each_category_has_reverse_items(self):
        """各カテゴリに逆転項目が少なくとも1問存在すること（バランス検証）"""
        for cat in CATEGORY_IDS:
            reverse_count = sum(1 for q in QUESTIONS if q["category"] == cat and q["reverse"])
            assert reverse_count >= 1, f"カテゴリ '{cat}' に逆転項目がありません"

    def test_explanation_not_empty(self):
        """全設問の explanation が空でないこと"""
        empty = [q["id"] for q in QUESTIONS if not q["explanation"].strip()]
        assert not empty, f"explanation が空の設問 ID: {empty}"

    def test_advice_high_not_empty(self):
        """全設問の advice_high が空でないこと"""
        empty = [q["id"] for q in QUESTIONS if not q["advice_high"].strip()]
        assert not empty, f"advice_high が空の設問 ID: {empty}"

    def test_advice_low_not_empty(self):
        """全設問の advice_low が空でないこと"""
        empty = [q["id"] for q in QUESTIONS if not q["advice_low"].strip()]
        assert not empty, f"advice_low が空の設問 ID: {empty}"


class TestQuestionById:
    """QUESTION_BY_ID 辞書の検証"""

    def test_all_questions_indexed(self):
        """QUESTION_BY_ID に全 120 問がインデックスされていること"""
        assert len(QUESTION_BY_ID) == 120

    def test_lookup_by_id(self):
        """任意の ID で設問が取得できること"""
        for qid in [1, 60, 120]:
            q = QUESTION_BY_ID.get(qid)
            assert q is not None, f"question_id={qid} が見つかりません"
            assert q["id"] == qid

    def test_unknown_id_returns_none(self):
        """存在しない ID は None を返すこと"""
        assert QUESTION_BY_ID.get(0) is None
        assert QUESTION_BY_ID.get(121) is None
        assert QUESTION_BY_ID.get(9999) is None

    def test_reference_same_object(self):
        """QUESTION_BY_ID の値は QUESTIONS リストと同一オブジェクトであること"""
        for q in QUESTIONS:
            assert QUESTION_BY_ID[q["id"]] is q
