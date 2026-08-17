#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

import requests

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"
CHARS = list("abcdefghijklmnopqrstuvwxyz0123456789")
DEFAULT_DELAY = 0.2


def load_keywords(path: Path) -> list[str]:
    if not path.exists():
        print(f"Fichier introuvable : {path}", file=sys.stderr)
        sys.exit(1)

    keywords = []
    seen = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        kw = line.strip().lower()
        if not kw or kw.startswith("#") or kw in seen:
            continue
        seen.add(kw)
        keywords.append(kw)

    if not keywords:
        print(f"Aucun keyword trouvé dans {path}", file=sys.stderr)
        sys.exit(1)

    return keywords


def fetch_suggestions(query: str, lang: str = "fr") -> list[str]:
    params = {
        "client": "firefox",
        "hl": lang,
        "q": query,
    }

    response = requests.get(AUTOCOMPLETE_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    if not isinstance(data, list) or len(data) < 2:
        return []

    return [suggestion.lower() for suggestion in data[1] if isinstance(suggestion, str)]


def expand_keyword(keyword: str, lang: str, delay: float) -> set[str]:
    results = set()
    queries = [keyword] + [f"{keyword} {char}" for char in CHARS]

    for query in queries:
        try:
            suggestions = fetch_suggestions(query, lang)
            results.update(suggestions)
            print(f"  {query!r} -> +{len(suggestions)} ({len(results)} total)")
        except Exception as exc:
            print(f"  {query!r} -> erreur: {exc}", file=sys.stderr)

        time.sleep(delay)

    return results


def scrape_keywords(
    input_keywords: list[str],
    lang: str = "fr",
    delay: float = DEFAULT_DELAY,
) -> set[str]:
    all_keywords = set()

    for index, keyword in enumerate(input_keywords, start=1):
        print(f"[{index}/{len(input_keywords)}] {keyword}")
        expanded = expand_keyword(keyword, lang, delay)
        all_keywords.update(expanded)
        print(f"  => {len(expanded)} suggestions, {len(all_keywords)} uniques au total\n")

    return all_keywords


def save_keywords(keywords: set[str], output_path: Path) -> None:
    output_path.write_text(
        "\n".join(sorted(keywords)) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Enrichit des keywords via l'autocomplete Google. "
            "Lit un fichier txt (1 keyword par ligne) et génère des suggestions réelles."
        )
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="input.txt",
        help="Fichier txt source avec les keywords à enrichir (défaut: input.txt)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="keywords.txt",
        help="Fichier de sortie (défaut: keywords.txt)",
    )
    parser.add_argument(
        "-l",
        "--lang",
        default="fr",
        help="Langue Google autocomplete (défaut: fr)",
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help="Délai entre chaque requête en secondes (défaut: 0.2)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    input_keywords = load_keywords(input_path)
    print(f"{len(input_keywords)} keywords chargés depuis {input_path}\n")

    enriched = scrape_keywords(input_keywords, lang=args.lang, delay=args.delay)
    save_keywords(enriched, output_path)

    print(f"{len(enriched)} keywords sauvegardés dans {output_path}")


if __name__ == "__main__":
    main()
