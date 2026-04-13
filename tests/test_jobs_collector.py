from collectors.jobs_collector import parse_feed_entry, filter_job, _extract_job_posting_schema, enrich_job_details


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


def test_extract_job_posting_schema():
        html = '''
        <html><head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": "Research Associate in AI",
            "description": "<p>Great role.</p>",
            "validThrough": "2026-05-01",
            "hiringOrganization": {"name": "Example University"},
            "jobLocation": {"address": {"addressLocality": "London", "addressCountry": "UK"}},
            "baseSalary": {"currency": "GBP", "value": {"minValue": 40000, "maxValue": 50000, "unitText": "YEAR"}}
        }
        </script>
        </head></html>
        '''
        posting = _extract_job_posting_schema(html)
        assert posting is not None
        assert posting["@type"] == "JobPosting"
        assert posting["title"] == "Research Associate in AI"


def test_enrich_job_details_from_job_posting(httpx_mock):
        httpx_mock.add_response(
                url="https://jobs.ac.uk/job/XYZ",
                text='''
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "JobPosting",
                    "description": "<p>Needs deep learning and MRI experience.</p>",
                    "validThrough": "2026-05-01",
                    "hiringOrganization": {"name": "Example University"},
                    "jobLocation": {"address": {"addressLocality": "London", "addressCountry": "UK"}},
                    "baseSalary": {"currency": "GBP", "value": {"minValue": 40000, "maxValue": 50000, "unitText": "YEAR"}}
                }
                </script>
                ''',
        )
        job = {
                "title": "Research Associate in AI",
                "url": "https://jobs.ac.uk/job/XYZ",
                "description": "Short summary",
                "source": "jobs.ac.uk",
                "deadline": "",
                "requirements_zh": "",
                "relevance_score": 0.0,
                "institution": "",
                "location": "",
                "salary": "",
        }
        enriched = enrich_job_details(job)
        assert enriched["institution"] == "Example University"
        assert enriched["deadline"] == "2026-05-01"
        assert enriched["location"] == "London, UK"
        assert enriched["salary"] == "GBP40000-GBP50000 YEAR"
        assert "deep learning" in enriched["description"]
