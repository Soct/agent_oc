"""Scrape les pages Wikichess pour constituer le corpus d'ouvertures."""

import asyncio
import html as html_mod
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

PAGES: list[int] = [
    # e4 lines
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    21, 22, 33,
    109, 113, 114, 116, 118, 123, 124, 125, 133, 134,
    502, 527, 789, 891, 894, 897,
    6414, 6700, 6701, 6702,
    # d4 lines
    35, 36, 37, 38, 39, 40, 41, 42,
    # More specific openings
    13873, 9806, 10816, 17305, 20122, 24363, 25036,
    32536, 38938, 43698, 50320, 53560, 56376,
    73725, 101961, 106948, 122751, 128842, 133563,
    205046, 232511, 267482,
]

MIN_TEXT_LENGTH = 60

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "wikichess_openings.json"


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

    # Extract descriptive text between date bracket and "====" separator
    desc_match = re.search(
        r'\[\d{4}\s+\w+\s+\d+\]\s*(.+?)={3,}',
        html,
        re.DOTALL,
    )
    desc_text = ""
    if desc_match:
        raw = desc_match.group(1).strip()
        # Clean HTML artifacts
        raw = re.sub(r'<[^>]+>', '', raw)
        raw = html_mod.unescape(raw)
        raw = re.sub(r'\s+', ' ', raw).strip()
        if len(raw) > 10:
            desc_text = raw

    # Extract move stats
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


async def main() -> None:
    results: list[dict[str, str]] = []
    seen_titles: set[str] = set()
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        for page_id in PAGES:
            url = f"https://ficgs.com/wikichess_{page_id}.html"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                # Wikichess serves Latin-1 despite sometimes declaring UTF-8
                html = resp.content.decode("latin-1")
            except httpx.HTTPError as exc:
                print(f"  SKIP {url}: {exc}")
                continue

            article = extract_article(html, page_id)
            if article and article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                results.append(article)
                print(f"  OK   {article['title']}")
            else:
                reason = "doublon" if article else "pas de contenu exploitable"
                print(f"  SKIP {url}: {reason}")

            await asyncio.sleep(0.4)

    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(results)} articles écrits dans {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
