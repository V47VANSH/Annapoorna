"""Unit tests for helper functions."""

import pytest

import chatbot
import predict
from docCrud.retrieve import chunk_text
from generateReport import bounding_box_to_polygon


class TestStripReasoning:
    def test_removes_think_block(self):
        assert chatbot._strip_reasoning("<think>musing</think>Answer") == "Answer"

    def test_leaves_plain_text_untouched(self):
        assert chatbot._strip_reasoning("  Answer  ") == "Answer"


class TestHistoryTrim:
    def test_short_history_is_untouched(self):
        history = [chatbot.HumanMessage(content=str(i)) for i in range(4)]
        assert chatbot._trim(history) == history

    def test_long_history_is_capped(self):
        history = [
            chatbot.HumanMessage(content=str(i))
            for i in range(chatbot.MAX_HISTORY_MESSAGES + 10)
        ]
        assert len(chatbot._trim(history)) == chatbot.MAX_HISTORY_MESSAGES

    def test_system_prompt_survives_trimming(self):
        history = [chatbot.SystemMessage(content="rules")]
        history += [
            chatbot.HumanMessage(content=str(i))
            for i in range(chatbot.MAX_HISTORY_MESSAGES + 10)
        ]

        trimmed = chatbot._trim(history)

        assert len(trimmed) == chatbot.MAX_HISTORY_MESSAGES
        assert trimmed[0].content == "rules"


class TestSessionIsolation:
    def test_sessions_do_not_share_history(self):
        chatbot.addContext("report for A", "user-a")
        chatbot.addContext("report for B", "user-b")

        assert "report for A" in chatbot._histories["user-a"][0].content
        assert "report for B" in chatbot._histories["user-b"][0].content

    def test_reset_only_clears_its_own_session(self):
        chatbot.addContext("report for A", "user-a")
        chatbot.addContext("report for B", "user-b")

        chatbot.resetConversation("user-a")

        assert "user-a" not in chatbot._histories
        assert "user-b" in chatbot._histories


class TestChunkText:
    def test_empty_text_yields_no_chunks(self):
        assert chunk_text("") == []

    def test_short_text_is_a_single_chunk(self):
        assert chunk_text("one two three") == ["one two three"]

    def test_chunks_overlap(self):
        words = " ".join(str(i) for i in range(120))
        chunks = chunk_text(words, max_words=50, overlap=10)

        assert len(chunks) > 1
        # 10 word overlap
        assert chunks[1].split()[0] == "40"

    def test_terminates_on_pathological_input(self):
        with pytest.raises(ValueError):
            chunk_text("a b c", max_words=10, overlap=10)


class TestBoundingBox:
    def test_produces_a_four_corner_ring(self):
        polygon = bounding_box_to_polygon([29.42, 29.43, 76.97, 76.98])
        assert len(polygon) == 4
        assert all(len(point) == 2 for point in polygon)

    def test_points_are_longitude_first(self):
        lat_min, lat_max, lon_min, lon_max = 29.42, 29.43, 76.97, 76.98
        polygon = bounding_box_to_polygon([lat_min, lat_max, lon_min, lon_max])

        assert [lon_min, lat_min] in polygon  # south-west
        assert [lon_max, lat_max] in polygon  # north-east

    def test_every_point_is_a_valid_coordinate(self):
        polygon = bounding_box_to_polygon([30.85, 30.95, 75.80, 75.90])
        for lon, lat in polygon:
            assert 75.80 <= lon <= 75.90
            assert 30.85 <= lat <= 30.95


class TestClassNames:
    def test_labels_are_unique(self):
        assert len(predict.CLASS_NAMES) == len(set(predict.CLASS_NAMES))

    def test_label_count_matches_trained_model(self):
        # must match the model's output layer
        assert len(predict.CLASS_NAMES) == 42

    def test_unavailable_model_raises_a_typed_error(self):
        with pytest.raises(predict.ModelUnavailable):
            predict.predict_disease(b"not-an-image")
