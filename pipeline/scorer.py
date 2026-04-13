import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential

_BATCH_SIZE = 8  # papers per batch-scoring call


def build_batch_paper_prompt(papers: list[dict]) -> str:
    lines = []
    for i, p in enumerate(papers):
        lines.append(f"[{i}] Title: {p['title']}\nAbstract: {p['abstract'][:500]}")
    block = "\n\n".join(lines)
    return (
        "Rate each arxiv paper's relevance to: Computer Vision, Medical Imaging "
        "(MRI/CT/ultrasound/pathology/fundus), Large Language Models, Vision-Language Models, "
        "Diffusion Models, Foundation Models for vision.\n\n"
        f"{block}\n\n"
        f"Reply with ONLY a JSON array of {len(papers)} integers 0-10 in order, e.g. [7,3,9,...]. "
        "No explanation."
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


def parse_batch_scores(text: str, expected: int) -> list[float]:
    """Parse a JSON array of scores from batch response."""
    try:
        match = re.search(r"\[[\d,\s]+\]", text)
        if match:
            arr = json.loads(match.group())
            scores = [max(0.0, min(10.0, float(s))) for s in arr]
            if len(scores) == expected:
                return scores
    except (json.JSONDecodeError, ValueError):
        pass
    # fallback: extract all numbers (including negative)
    nums = re.findall(r"-?\d+(?:\.\d+)?", text)
    scores = [max(0.0, min(10.0, float(n))) for n in nums[:expected]]
    while len(scores) < expected:
        scores.append(0.0)
    return scores


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _call_llm(client: Any, model: str, prompt: str, max_tokens: int = 50) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0,
    )
    return resp.choices[0].message.content


def _score_batch(batch: list[dict], client: Any, model: str) -> list[dict]:
    """Score a batch of papers in a single LLM call."""
    prompt = build_batch_paper_prompt(batch)
    raw = _call_llm(client, model, prompt, max_tokens=len(batch) * 5 + 20)
    scores = parse_batch_scores(raw, len(batch))
    for paper, score in zip(batch, scores):
        paper["score"] = score
    return batch


def score_papers(
    papers: list[dict],
    client: Any,
    model: str,
    threshold: float,
) -> list[dict]:
    """Score papers using batched + concurrent LLM calls."""
    if not papers:
        return []

    batches = [papers[i:i + _BATCH_SIZE] for i in range(0, len(papers), _BATCH_SIZE)]
    scored_papers: list[dict] = []

    with ThreadPoolExecutor(max_workers=min(8, len(batches))) as executor:
        futures = {executor.submit(_score_batch, batch, client, model): batch
                   for batch in batches}
        for future in as_completed(futures):
            try:
                batch_result = future.result()
                scored_papers.extend(batch_result)
            except Exception as e:
                # fallback: mark batch as 0
                for paper in futures[future]:
                    paper["score"] = 0.0
                scored_papers.extend(futures[future])
                print(f"  Batch scoring error: {e}")

    return [p for p in scored_papers if p["score"] >= threshold]


def _score_single_job(job: dict, client: Any, model: str) -> dict:
    prompt = build_job_prompt(job)
    raw = _call_llm(client, model, prompt)
    job["relevance_score"] = parse_score(raw)
    return job


def score_jobs(
    jobs: list[dict],
    client: Any,
    model: str,
    threshold: float,
) -> list[dict]:
    """Score jobs concurrently."""
    if not jobs:
        return []

    scored: list[dict] = []
    with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as executor:
        futures = {executor.submit(_score_single_job, job, client, model): job
                   for job in jobs}
        for future in as_completed(futures):
            try:
                scored.append(future.result())
            except Exception as e:
                job = futures[future]
                job["relevance_score"] = 0.0
                scored.append(job)
                print(f"  Job scoring error: {e}")

    return [j for j in scored if j["relevance_score"] >= threshold]
