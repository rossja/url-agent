import json, os
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI
from mcp.server.fastmcp import FastMCP

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
client = OpenAI()
mcp = FastMCP("url-agent-single-pass-planner")

def fetch(url: str, timeout=20) -> tuple[str, list[str]]:
    r = httpx.get(url, timeout=timeout, follow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    links = [a.get("href") for a in soup.find_all("a", href=True)]
    links = [urljoin(url, h) for h in links if h]
    return text[:20000], links[:60]

def same_origin(root: str, u: str) -> bool:
    return urlparse(root).netloc == urlparse(u).netloc

def plan(root_url: str, root_text: str, root_links: list[str], max_depth: int, max_pages: int) -> dict:
    prompt = {
        "task": "Plan a bounded crawl for understanding a URL well enough to implement the feature it describes.",
        "constraints": {"max_depth": max_depth, "max_pages": max_pages, "same_origin_only": True},
        "root_url": root_url,
        "root_excerpt": root_text[:4000],
        "candidate_links": [u for u in root_links if same_origin(root_url, u)][:30],
        "output_schema": {
            "fetch": [{"url": "string", "depth": "int", "why": "string"}],
            "final_output_format": {
                "feature_summary": "string",
                "key_requirements": ["string"],
                "interfaces_or_artifacts": ["string"],
                "edge_cases": ["string"],
                "implementation_notes": ["string"]
            }
        }
    }

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a planner. Return ONLY valid JSON matching the requested schema."},
            {"role": "user", "content": json.dumps(prompt)}
        ],
    )
    return json.loads(resp.choices[0].message.content)

def synthesize(plan_obj: dict, corpus: list[dict]) -> dict:
    payload = {"plan": plan_obj, "pages": corpus}
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Produce the final output EXACTLY in the plan's final_output_format keys. Return ONLY JSON."},
            {"role": "user", "content": json.dumps(payload)[:240000]},
        ],
    )
    return json.loads(resp.choices[0].message.content)

@mcp.tool()
def summarize_url(url: str, max_depth: int = 2, max_pages: int = 4) -> str:
    root_text, root_links = fetch(url)
    plan_obj = plan(url, root_text, root_links, max_depth, max_pages)

    visited = set()
    corpus = []

    visited.add(url)
    corpus.append({"url": url, "depth": 0, "text": root_text[:12000]})

    for item in plan_obj.get("fetch", [])[:max_pages]:
        u = item.get("url")
        d = int(item.get("depth", 1))
        if not u or u in visited or d > max_depth or not same_origin(url, u):
            continue
        t, _ = fetch(u)
        visited.add(u)
        corpus.append({"url": u, "depth": d, "text": t[:12000]})

    out = synthesize(plan_obj, corpus)
    return json.dumps(out, indent=2)

if __name__ == "__main__":
    mcp.run()
