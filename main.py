#!/usr/bin/env python3
import argparse
import sys
import time
from pathlib import Path

import requests

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"
CHARS = list("abcdefghijklmnopqrstuvwxyz0123456789")
DEFAULT_DELAY = 0.2
MIN_WORDS = 1
MAX_WORDS = 3
MAX_PER_PREFIX = 5
MAX_PER_SEED = 40


def is_valid_keyword(keyword: str, seed: str = "", direct: set[str] | None = None) -> bool:
    words = keyword.split()
    direct = direct or set()

    if not (MIN_WORDS <= len(words) <= MAX_WORDS):
        return False

    if any(char.isdigit() for char in keyword):
        return False

    if len(words) != len(set(words)):
        return False

    if len(words[-1]) <= 2 and keyword not in direct:
        return False

    if seed:
        seed_words = set(seed.split())
        if not seed_words.intersection(words):
            return False

    return True


def prefix_key(keyword: str) -> str:
    words = keyword.split()
    if len(words) == 1:
        return words[0]
    return " ".join(words[:2])


def dedupe_repetitive(
    keywords: set[str],
    direct: set[str] | None = None,
    max_per_prefix: int = MAX_PER_PREFIX,
) -> set[str]:
    direct = direct or set()
    buckets: dict[str, int] = {}
    kept: set[str] = set()

    def rank(keyword: str) -> tuple:
        return (
            0 if keyword in direct else 1,
            len(keyword.split()),
            len(keyword),
            keyword,
        )

    for keyword in sorted(keywords, key=rank):
        key = prefix_key(keyword)
        if buckets.get(key, 0) >= max_per_prefix:
            continue
        buckets[key] = buckets.get(key, 0) + 1
        kept.add(keyword)

    return kept


def filter_keywords(
    raw_keywords: set[str],
    seed: str = "",
    direct: set[str] | None = None,
    max_per_seed: int = MAX_PER_SEED,
) -> set[str]:
    valid = {kw for kw in raw_keywords if is_valid_keyword(kw, seed=seed, direct=direct)}
    deduped = dedupe_repetitive(valid, direct=direct)

    if len(deduped) <= max_per_seed:
        return deduped

    def rank(keyword: str) -> tuple:
        return (
            0 if direct and keyword in direct else 1,
            len(keyword.split()),
            len(keyword),
            keyword,
        )

    ranked = sorted(deduped, key=rank)
    return set(ranked[:max_per_seed])


def load_keywords(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    keywords = []
    seen = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        kw = line.strip().lower()
        if not kw or kw.startswith("#") or kw in seen:
            continue
        seen.add(kw)
        keywords.append(kw)

    if not keywords:
        raise ValueError(f"Aucun keyword trouvé dans {path}")

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


def expand_keyword(keyword: str, lang: str, delay: float) -> tuple[set[str], set[str]]:
    results: set[str] = set()
    direct: set[str] = set()
    queries = [keyword] + [f"{keyword} {char}" for char in CHARS]

    for query in queries:
        try:
            suggestions = fetch_suggestions(query, lang)
            results.update(suggestions)
            if query == keyword:
                direct.update(suggestions)
            print(f"  {query!r} -> +{len(suggestions)} ({len(results)} total)")
        except Exception as exc:
            print(f"  {query!r} -> erreur: {exc}", file=sys.stderr)

        time.sleep(delay)

    return results, direct


def scrape_keywords(
    input_keywords: list[str],
    lang: str = "fr",
    delay: float = DEFAULT_DELAY,
) -> set[str]:
    all_keywords: set[str] = set()
    total_raw = 0
    total_filtered = 0

    for index, keyword in enumerate(input_keywords, start=1):
        print(f"[{index}/{len(input_keywords)}] {keyword}")
        expanded, direct = expand_keyword(keyword, lang, delay)
        total_raw += len(expanded)

        cleaned = filter_keywords(expanded, seed=keyword, direct=direct)
        total_filtered += len(cleaned)
        all_keywords.update(cleaned)

        print(
            f"  => {len(expanded)} brutes -> {len(cleaned)} retenues "
            f"({len(all_keywords)} uniques au total)\n"
        )

    print(
        f"Filtrage : {total_raw} brutes -> {total_filtered} retenues "
        f"({len(all_keywords)} uniques, 1-{MAX_WORDS} mots, max {MAX_PER_PREFIX}/préfixe)\n"
    )

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


def run_scraper(
    input_path: Path,
    output_path: Path | None = None,
    lang: str = "fr",
    delay: float = DEFAULT_DELAY,
) -> tuple[int, Path]:
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_keywords.txt")

    input_keywords = load_keywords(input_path)
    print(f"{len(input_keywords)} keywords chargés depuis {input_path}\n")

    enriched = scrape_keywords(input_keywords, lang=lang, delay=delay)
    save_keywords(enriched, output_path)

    print(f"{len(enriched)} keywords sauvegardés dans {output_path}")
    return len(enriched), output_path


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        run_scraper(input_path, output_path, lang=args.lang, delay=args.delay)
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
