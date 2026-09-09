"""Scrape récursif de Wikichess pour constituer le corpus d'ouvertures."""

import asyncio
import html as html_mod
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

SEED_URL = "https://ficgs.com/wikichess.html"
BASE_URL = "https://ficgs.com/wikichess_{}.html"
MAX_PAGES = 2000
MIN_TEXT_LENGTH = 60
CONCURRENCY = 5
DELAY = 0.3

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "wikichess_openings.json"


def _extract_linked_ids(html: str) -> set[int]:
    return {int(m) for m in re.findall(r'wikichess_(\d+)\.html', html) if m != "0"}


def extract_article(html: str, page_id: int) -> dict[str, str] | None:
    """Extract opening name, description and stats from a Wikichess HTML page."""
    eco_match = re.search(r'\[ECO "([^"]+)"\]', html)
    opening_match = re.search(r'\[Opening "([^"]+)"\]', html)
    variation_match = re.search(r'\[Variation "([^"]+)"\]', html)

    if not opening_match:
        return None

    title = opening_match.group(1)
    if variation_match:
        title += f" — {variation_match.group(1)}"
    eco = eco_match.group(1) if eco_match else ""

    desc_match = re.search(
        r'\[\d{4}\s+\w+\s+\d+\]\s*(.+?)={3,}',
        html,
        re.DOTALL,
    )
    desc_text = ""
    if desc_match:
        raw = desc_match.group(1).strip()
        raw = re.sub(r'<[^>]+>', '', raw)
        raw = html_mod.unescape(raw)
        raw = re.sub(r'\s+', ' ', raw).strip()
        if len(raw) > 10:
            desc_text = raw

    stat_lines: list[str] = []
    for m in re.finditer(
        r'(\w[\w\+\#]*)\s*:\s*(\d+)\s*games?,\s*White ELO av\s*:\s*(\d+)',
        html,
    ):
        move, games, elo = m.group(1), m.group(2), m.group(3)
        stat_lines.append(f"{move} ({games} parties, ELO moy. {elo})")

    stats_text = ""
    if stat_lines:
        stats_text = "Coups joués : " + " ; ".join(stat_lines[:8]) + "."

    text = " ".join(filter(None, [desc_text, stats_text]))
    if not text or len(text) < MIN_TEXT_LENGTH:
        return None

    return {
        "title": f"{eco} {title}".strip() if eco else title,
        "text": text,
        "source_url": f"https://ficgs.com/wikichess_{page_id}.html",
    }


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content.decode("latin-1")
    except httpx.HTTPError as exc:
        print(f"  SKIP {url}: {exc}")
        return None


async def main() -> None:
    visited: set[int] = set()
    queue: list[int] = []
    results: list[dict[str, str]] = []
    seen_titles: set[str] = set()
    sem = asyncio.Semaphore(CONCURRENCY)

    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        # Discover seed page IDs from the index
        index_html = await _fetch(client, SEED_URL)
        if index_html:
            queue.extend(sorted(_extract_linked_ids(index_html)))

        while queue and len(visited) < MAX_PAGES:
            page_id = queue.pop(0)
            if page_id in visited:
                continue
            visited.add(page_id)

            async with sem:
                html = await _fetch(client, BASE_URL.format(page_id))
            if not html:
                continue

            # Discover linked sub-pages
            for linked_id in _extract_linked_ids(html):
                if linked_id not in visited:
                    queue.append(linked_id)

            article = extract_article(html, page_id)
            if article and article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                results.append(article)
                print(f"  OK   [{len(results):>4}] {article['title']}")
            else:
                reason = "doublon" if article else "pas de contenu exploitable"
                print(f"  SKIP wikichess_{page_id}: {reason}")

            await asyncio.sleep(DELAY)

    results.sort(key=lambda a: a["title"])
    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(results)} articles écrits dans {OUTPUT}  (pages visitées : {len(visited)})")


if __name__ == "__main__":
    asyncio.run(main())
