from unittest.mock import patch, MagicMock
from pipeline.scorer import build_paper_prompt, parse_score, score_papers


def test_build_paper_prompt_contains_title(sample_paper):
    prompt = build_paper_prompt(sample_paper)
    assert "FoundationSeg" in prompt
    assert "0-10" in prompt


def test_parse_score_extracts_integer():
    assert parse_score("Score: 8") == 8.0
    assert parse_score("I would rate this 7/10") == 7.0
    assert parse_score("9") == 9.0


def test_parse_score_clamps_to_range():
    assert parse_score("11") == 10.0
    assert parse_score("-1") == 0.0


def test_parse_score_returns_zero_on_garbage():
    assert parse_score("No numeric content here!") == 0.0


def test_score_papers_attaches_scores(sample_paper):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Score: 8"))]
    )
    results = score_papers([sample_paper], client=mock_client, model="test-model", threshold=6)
    assert len(results) == 1
    assert results[0]["score"] == 8.0


def test_score_papers_filters_below_threshold(sample_paper):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Score: 3"))]
    )
    results = score_papers([sample_paper], client=mock_client, model="test-model", threshold=6)
    assert len(results) == 0
