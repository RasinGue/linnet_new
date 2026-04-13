from collectors.arxiv_collector import keyword_match, fetch_papers


def test_keyword_match_positive():
    text = "A foundation model for medical image segmentation using MRI and CT scans"
    must_include = ["medical image", "MRI", "CT scan", "segmentation"]
    assert keyword_match(text, must_include) is True


def test_keyword_match_negative():
    text = "A graph neural network for protein folding prediction"
    must_include = ["medical image", "MRI", "CT scan", "segmentation"]
    assert keyword_match(text, must_include) is False


def test_keyword_match_case_insensitive():
    text = "MEDICAL IMAGING with Diffusion Models"
    must_include = ["medical imaging"]
    assert keyword_match(text, must_include) is True


def test_fetch_papers_returns_list():
    """fetch_papers with zero max_results returns empty list without hitting network."""
    results = fetch_papers(categories=["cs.CV"], must_include=["medical"], max_results=0)
    assert isinstance(results, list)
