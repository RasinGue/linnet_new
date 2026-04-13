from collectors.jobs_collector import parse_feed_entry, filter_job


def test_filter_job_passes_relevant():
    job = {
        "title": "Postdoc in Medical Imaging AI",
        "description": "We seek candidates with expertise in deep learning for MRI segmentation.",
    }
    assert filter_job(
        job,
        include_keywords=["medical imaging", "deep learning", "postdoc"],
        exclude_keywords=["chemistry"],
    ) is True


def test_filter_job_blocks_excluded():
    job = {
        "title": "Research Associate in Computational Chemistry",
        "description": "Machine learning for drug discovery and molecular modelling.",
    }
    assert filter_job(
        job,
        include_keywords=["machine learning", "research associate"],
        exclude_keywords=["chemistry"],
    ) is False


def test_filter_job_blocks_irrelevant():
    job = {
        "title": "Lecturer in Economics",
        "description": "Teaching undergraduate economics and supervising postgraduates.",
    }
    assert filter_job(
        job,
        include_keywords=["computer vision", "LLM", "deep learning"],
        exclude_keywords=["economics"],
    ) is False


def test_parse_feed_entry_extracts_fields():
    entry = type("Entry", (), {
        "title": "Research Associate in AI",
        "link": "https://jobs.ac.uk/job/XYZ",
        "summary": "Deadline: 1 May 2026. Requires deep learning expertise.",
        "published": "Mon, 13 Apr 2026 09:00:00 +0000",
    })()
    job = parse_feed_entry(entry, source_name="jobs.ac.uk")
    assert job["title"] == "Research Associate in AI"
    assert job["url"] == "https://jobs.ac.uk/job/XYZ"
    assert job["source"] == "jobs.ac.uk"
    assert "description" in job
