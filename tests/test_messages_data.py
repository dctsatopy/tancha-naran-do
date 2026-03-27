"""
メッセージデータ (app/messages_data.py) のユニットテスト

仕様参照: tancha_naran_do.md §3.3
"""
import pytest
from app.messages_data import RELAXATION_MESSAGES, get_random_message, get_messages


class TestRelaxationMessages:
    """RELAXATION_MESSAGES リストの内容検証"""

    def test_minimum_message_count(self):
        """リラクゼーションメッセージが 50 件以上あること（仕様 §3.3）"""
        assert len(RELAXATION_MESSAGES) >= 50

    def test_all_messages_have_text(self):
        """全メッセージに text フィールドがあり空でないこと"""
        for i, m in enumerate(RELAXATION_MESSAGES):
            assert "text" in m, f"index={i}: text フィールドなし"
            assert m["text"].strip(), f"index={i}: text が空"

    def test_all_messages_have_author_key(self):
        """全メッセージに author キーがあること（値は空文字も可）"""
        for i, m in enumerate(RELAXATION_MESSAGES):
            assert "author" in m, f"index={i}: author フィールドなし"

    def test_unique_message_texts(self):
        """メッセージの text に重複がないこと"""
        texts = [m["text"] for m in RELAXATION_MESSAGES]
        assert len(set(texts)) == len(texts), "メッセージに重複があります"


class TestGetRandomMessage:
    """get_random_message() の検証"""

    def test_returns_dict(self):
        """dict が返ること"""
        msg = get_random_message()
        assert isinstance(msg, dict)

    def test_returned_dict_has_text(self):
        """返り値に text キーがあること"""
        msg = get_random_message()
        assert "text" in msg
        assert msg["text"]

    def test_returns_message_from_list(self):
        """返り値が RELAXATION_MESSAGES の要素であること"""
        msg = get_random_message()
        assert msg in RELAXATION_MESSAGES


class TestGetMessages:
    """get_messages() の検証"""

    def test_returns_correct_count(self):
        """指定した件数のメッセージが返ること"""
        msgs = get_messages(3)
        assert len(msgs) == 3

    def test_returns_count_of_2(self):
        """count=2 でリスト長が 2 になること（result 画面で使用）"""
        msgs = get_messages(2)
        assert len(msgs) == 2

    def test_no_duplicates_in_result(self):
        """返ったメッセージに重複がないこと"""
        msgs = get_messages(10)
        texts = [m["text"] for m in msgs]
        assert len(texts) == len(set(texts))

    def test_count_exceeds_total_is_capped(self):
        """要求件数がリスト総数を超えた場合はリスト総数を返すこと"""
        msgs = get_messages(10000)
        assert len(msgs) == len(RELAXATION_MESSAGES)

    def test_all_returned_from_list(self):
        """返り値がすべて RELAXATION_MESSAGES の要素であること"""
        msgs = get_messages(5)
        for m in msgs:
            assert m in RELAXATION_MESSAGES
