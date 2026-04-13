import re
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential


def build_paper_prompt(paper: dict) -> str:
    return (
        "Rate this arxiv paper's relevance to the following research areas "
        "on a scale of 0-10: Computer Vision, Medical Imaging (MRI/CT/ultrasound/"
        "pathology/fundus), Large Language Models, Vision-Language Models, "
        "Diffusion Models, Foundation Models for vision.\n\n"
        f"Title: {paper['title']}\n"
        f"Abstract: {paper['abstract'][:800]}\n\n"
        "Reply with ONLY a single integer score 0-10. "
        "10=directly core to these fields, 0=completely unrelated."
    )


def build_job_prompt(job: dict) -> str:
    return (
        "Rate this academic job posting's relevance to a researcher specialising in "
        "Computer Vision, Medical Imaging, LLM, VLM on a scale of 0-10.\n\n"
        f"Title: {job['title']}\n"
        f"Description: {job.get('description', '')[:600]}\n\n"
        "Reply with ONLY a single integer score 0-10."
    )


def parse_score(text: str) -> float:
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
    if not numbers:
        return 0.0
    score = float(numbers[0])
    return max(0.0, min(10.0, score))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _call_llm(client: Any, model: str, prompt: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0,
    )
    return resp.choices[0].message.content


def score_papers(
    papers: list[dict],
    client: Any,
    model: str,
    threshold: float,
) -> list[dict]:
    scored = []
    for paper in papers:
        prompt = build_paper_prompt(paper)
        raw = _call_llm(client, model, prompt)
        paper["score"] = parse_score(raw)
        if paper["score"] >= threshold:
            scored.append(paper)
    return scored


def score_jobs(
    jobs: list[dict],
    client: Any,
    model: str,
    threshold: float,
) -> list[dict]:
    scored = []
    for job in jobs:
        prompt = build_job_prompt(job)
        raw = _call_llm(client, model, prompt)
        job["relevance_score"] = parse_score(raw)
        if job["relevance_score"] >= threshold:
            scored.append(job)
    return scored
