#!/usr/bin/env python3
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests

from config import (
    CASELESS_LANGS,
    DEFAULT_LANG,
    DEFAULT_PRESET_ID,
    LanguageProfile,
    get_google_hl,
    get_lang_profile,
    get_preset,
    normalize_lang,
)

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"
DEFAULT_DELAY = 0.15
MIN_WORDS = 1
MAX_WORDS = 3
MAX_PER_PREFIX = 3
MAX_PER_ROOT = 2
MAX_PER_SEED = 25
MAX_MODIFIERS = 8

CJK_RANGES = (
    (0x3040, 0x30FF),  # Hiragana + Katakana
    (0x4E00, 0x9FFF),  # CJK Unified
    (0xAC00, 0xD7AF),  # Hangul
)


@dataclass
class ThemeProfile:
    seed_words: set[str] = field(default_factory=set)
    seed_bigrams: set[str] = field(default_factory=set)
    stopwords: frozenset[str] = field(default_factory=frozenset)


def is_cjk_lang(lang: str) -> bool:
    return normalize_lang(lang) in CASELESS_LANGS or normalize_lang(lang).startswith("zh")


def has_cjk_chars(text: str) -> bool:
    for char in text:
        code = ord(char)
        for start, end in CJK_RANGES:
            if start <= code <= end:
                return True
    return False


def normalize_keyword(text: str, lang: str) -> str:
    if is_cjk_lang(lang):
        return text.strip()
    return text.strip().lower()


def build_theme_profile(seeds: list[str], lang: str = DEFAULT_LANG) -> ThemeProfile:
    """Construit le profil thématique depuis les seeds — 100% dynamique, aucune liste hardcodée."""
    profile = get_lang_profile(lang)
    stopwords = profile.stopwords
    cjk = is_cjk_lang(lang)
    seed_words: set[str] = set()
    seed_bigrams: set[str] = set()

    for seed in seeds:
        normalized = normalize_keyword(seed, lang)
        parts = normalized.replace("-", " ").split()
        meaningful = []
        for w in parts:
            wl = w if cjk else w.lower()
            if wl in stopwords:
                continue
            min_len = 2 if cjk else 3
            if len(wl) >= min_len:
                seed_words.add(wl)
                meaningful.append(wl)
        for i in range(len(meaningful) - 1):
            seed_bigrams.add(f"{meaningful[i]} {meaningful[i + 1]}")

    return ThemeProfile(
        seed_words=seed_words,
        seed_bigrams=seed_bigrams,
        stopwords=stopwords,
    )


def build_dynamic_modifiers(
    seeds: list[str],
    lang_profile: LanguageProfile,
    lang: str = DEFAULT_LANG,
) -> list[str]:
    """
    Modifiers = mots non-stopword présents dans ≥ 2 seeds différents.
    Entièrement dérivés des seeds — aucun terme prédéfini.
    Limité à MAX_MODIFIERS pour contrôler le volume de requêtes.
    """
    stopwords = lang_profile.stopwords
    cjk = is_cjk_lang(lang)
    word_seed_count: dict[str, int] = {}

    for seed in seeds:
        normalized = normalize_keyword(seed, lang)
        seen_in_seed: set[str] = set()
        for w in normalized.replace("-", " ").split():
            wl = w if cjk else w.lower()
            if wl in stopwords or len(wl) < (2 if cjk else 3):
                continue
            if wl not in seen_in_seed:
                word_seed_count[wl] = word_seed_count.get(wl, 0) + 1
                seen_in_seed.add(wl)

    dominant = sorted(
        (w for w, cnt in word_seed_count.items() if cnt >= 2),
        key=lambda w: (-word_seed_count[w], w),
    )

    return dominant[:MAX_MODIFIERS]


def is_valid_form(keyword: str, lang: str = DEFAULT_LANG) -> bool:
    """Validation structurelle uniquement — indépendante de la niche."""
    words = keyword.split()

    if not (MIN_WORDS <= len(words) <= MAX_WORDS):
        return False

    if any(ch.isdigit() for ch in keyword):
        return False

    if any(c in keyword for c in ".,;:!?()[]{}"):
        return False

    if len(words) != len(set(words)):
        return False

    min_tail = 1 if is_cjk_lang(lang) else 2
    if len(words[-1]) <= min_tail:
        return False

    return True


def is_on_theme(
    keyword: str,
    seed: str,
    theme_profile: ThemeProfile,
    lang: str = DEFAULT_LANG,
) -> bool:
    """
    Un keyword est dans le thème si :
    1. Au moins 1 mot du seed est présent dans le keyword (cohérence seed)
    2. Au moins 1 mot du keyword est dans seed_words OU un bigramme dans seed_bigrams
       (ancrage thème dynamique)
    """
    cjk = is_cjk_lang(lang)
    kw_words = keyword.split()
    kw_set = set(kw_words)

    seed_norm = normalize_keyword(seed, lang)
    seed_parts = set(seed_norm.replace("-", " ").split())

    # Condition 1 : cohérence seed
    if not seed_parts.intersection(kw_set):
        if not cjk:
            return False
        seed_lower = {w.lower() for w in seed_parts}
        kw_lower = {w.lower() for w in kw_set}
        if not seed_lower.intersection(kw_lower):
            return False

    # Condition 2 : ancrage thème
    has_theme_word = bool(kw_set.intersection(theme_profile.seed_words))
    if not has_theme_word:
        kw_bigrams = {
            f"{kw_words[i]} {kw_words[i + 1]}" for i in range(len(kw_words) - 1)
        }
        has_theme_word = bool(kw_bigrams.intersection(theme_profile.seed_bigrams))

    return has_theme_word


def is_valid_keyword(
    keyword: str,
    seed: str = "",
    theme_profile: ThemeProfile | None = None,
    lang: str = DEFAULT_LANG,
) -> bool:
    if not is_valid_form(keyword, lang):
        return False
    if seed and theme_profile is not None:
        if not is_on_theme(keyword, seed, theme_profile, lang):
            return False
    return True


def prefix_key(keyword: str, stopwords: frozenset[str] = frozenset()) -> str:
    words = keyword.split()
    specific = [w for w in words if w not in stopwords]
    if len(specific) >= 2:
        return " ".join(specific[:2])
    if specific:
        return specific[0]
    if len(words) >= 2:
        return " ".join(words[:2])
    return words[0]


def root_key(keyword: str, stopwords: frozenset[str] = frozenset()) -> str:
    words = keyword.split()
    specific = [w for w in words if w not in stopwords]
    if len(specific) >= 2:
        return f"{specific[0]}|{specific[-1]}"
    if specific:
        return specific[0]
    return words[0]


def dedupe_repetitive(
    keywords: set[str],
    direct: set[str] | None = None,
    max_per_prefix: int = MAX_PER_PREFIX,
    stopwords: frozenset[str] = frozenset(),
) -> set[str]:
    direct = direct or set()
    buckets: dict[str, int] = {}
    kept: set[str] = set()

    def rank(keyword: str) -> tuple:
        return (0 if keyword in direct else 1, len(keyword.split()), len(keyword), keyword)

    for keyword in sorted(keywords, key=rank):
        key = prefix_key(keyword, stopwords)
        if buckets.get(key, 0) >= max_per_prefix:
            continue
        buckets[key] = buckets.get(key, 0) + 1
        kept.add(keyword)

    return kept


def global_dedupe(
    keywords: set[str],
    direct: set[str] | None = None,
    max_per_root: int = MAX_PER_ROOT,
    stopwords: frozenset[str] = frozenset(),
) -> set[str]:
    direct = direct or set()
    buckets: dict[str, int] = {}
    kept: set[str] = set()

    def rank(keyword: str) -> tuple:
        return (0 if keyword in direct else 1, len(keyword.split()), len(keyword), keyword)

    for keyword in sorted(keywords, key=rank):
        key = root_key(keyword, stopwords)
        if buckets.get(key, 0) >= max_per_root:
            continue
        buckets[key] = buckets.get(key, 0) + 1
        kept.add(keyword)

    return kept


def filter_keywords(
    raw_keywords: set[str],
    seed: str,
    theme_profile: ThemeProfile,
    direct: set[str],
    lang: str = DEFAULT_LANG,
    max_per_seed: int = MAX_PER_SEED,
    max_per_prefix: int = MAX_PER_PREFIX,
) -> set[str]:
    stopwords = theme_profile.stopwords

    valid = {
        kw for kw in raw_keywords
        if is_valid_keyword(kw, seed=seed, theme_profile=theme_profile, lang=lang)
    }
    deduped = dedupe_repetitive(valid, direct=direct, max_per_prefix=max_per_prefix, stopwords=stopwords)

    if len(deduped) <= max_per_seed:
        return deduped

    def rank(keyword: str) -> tuple:
        return (0 if keyword in direct else 1, len(keyword.split()), len(keyword), keyword)

    return set(sorted(deduped, key=rank)[:max_per_seed])


def load_keywords(path: Path, lang: str = DEFAULT_LANG) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {path}")

    keywords = []
    seen = set()

    for line in path.read_text(encoding="utf-8").splitlines():
        kw = normalize_keyword(line, lang)
        if not kw or kw.startswith("#") or kw in seen:
            continue
        seen.add(kw)
        keywords.append(kw)

    if not keywords:
        raise ValueError(f"Aucun keyword trouvé dans {path}")

    return keywords


def fetch_suggestions(query: str, lang: str = DEFAULT_LANG) -> list[str]:
    hl = get_google_hl(lang)
    params = {"client": "firefox", "hl": hl, "q": query}
    headers = {"User-Agent": "Mozilla/5.0"}

    for attempt in range(4):
        try:
            response = requests.get(AUTOCOMPLETE_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, list) or len(data) < 2:
                return []
            return [
                normalize_keyword(s, lang)
                for s in data[1]
                if isinstance(s, str)
            ]
        except Exception as exc:
            if attempt == 3:
                raise
            wait = 2 ** attempt
            print(f"  retry {attempt + 1}/3 dans {wait}s ({exc})", file=sys.stderr)
            time.sleep(wait)

    return []  # unreachable


def expand_seed(
    seed: str,
    modifiers: list[str],
    lang: str,
    delay: float,
) -> tuple[set[str], set[str]]:
    results: set[str] = set()
    direct: set[str] = set()

    seed_words = set(normalize_keyword(seed, lang).split())
    queries = [seed] + [
        f"{seed} {mod}"
        for mod in modifiers
        if mod not in seed_words
    ]

    for query in queries:
        try:
            suggestions = fetch_suggestions(query, lang)
            results.update(suggestions)
            if query == seed:
                direct.update(suggestions)
            print(f"  {query!r} -> +{len(suggestions)} ({len(results)} total)")
        except Exception as exc:
            print(f"  {query!r} -> erreur: {exc}", file=sys.stderr)
        time.sleep(delay)

    return results, direct


def scrape_keywords(
    input_keywords: list[str],
    lang: str = DEFAULT_LANG,
    delay: float = DEFAULT_DELAY,
    max_per_seed: int = MAX_PER_SEED,
    max_per_prefix: int = MAX_PER_PREFIX,
    max_per_root: int = MAX_PER_ROOT,
) -> set[str]:
    profile = get_lang_profile(lang)
    theme_profile = build_theme_profile(input_keywords, lang)
    modifiers = build_dynamic_modifiers(input_keywords, profile, lang)
    all_keywords: set[str] = set()
    all_direct: set[str] = set()
    total_raw = 0
    total_filtered = 0

    print(
        f"Source : Google autocomplete (hl={get_google_hl(lang)}) | "
        f"langue : {profile.label}\n"
        f"Limites : {max_per_seed}/seed, {max_per_prefix}/préfixe, {max_per_root}/racine\n"
        f"Thème : {len(theme_profile.seed_words)} mots, "
        f"{len(theme_profile.seed_bigrams)} bigrammes\n"
        f"Modifiers ({len(modifiers)}) : {', '.join(modifiers)}\n"
    )

    for index, seed in enumerate(input_keywords, start=1):
        print(f"[{index}/{len(input_keywords)}] {seed}")
        expanded, direct = expand_seed(seed, modifiers, lang, delay)
        total_raw += len(expanded)
        all_direct.update(direct)

        cleaned = filter_keywords(
            expanded,
            seed=seed,
            theme_profile=theme_profile,
            direct=direct,
            lang=lang,
            max_per_seed=max_per_seed,
            max_per_prefix=max_per_prefix,
        )
        total_filtered += len(cleaned)
        all_keywords.update(cleaned)

        print(
            f"  => {len(expanded)} brutes -> {len(cleaned)} retenues "
            f"({len(all_keywords)} uniques au total)\n"
        )

    before_global = len(all_keywords)
    all_keywords = global_dedupe(
        all_keywords,
        direct=all_direct,
        max_per_root=max_per_root,
        stopwords=theme_profile.stopwords,
    )

    print(
        f"Filtrage : {total_raw} brutes -> {total_filtered} retenues "
        f"-> {before_global} uniques -> {len(all_keywords)} après dédup globale\n"
    )

    return all_keywords


def save_keywords(keywords: set[str], output_path: Path) -> None:
    output_path.write_text(
        "\n".join(sorted(keywords)) + "\n",
        encoding="utf-8",
    )


def run_scraper(
    input_path: Path,
    output_path: Path | None = None,
    lang: str = DEFAULT_LANG,
    delay: float = DEFAULT_DELAY,
    preset_id: str = DEFAULT_PRESET_ID,
) -> tuple[int, Path]:
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_keywords.txt")

    preset = get_preset(preset_id)
    profile = get_lang_profile(lang)
    input_keywords = load_keywords(input_path, lang)
    print(f"{len(input_keywords)} keywords chargés depuis {input_path}")
    print(f"Preset : {preset.label} | Langue : {profile.label} ({get_google_hl(lang)})\n")

    enriched = scrape_keywords(
        input_keywords,
        lang=lang,
        delay=delay,
        max_per_seed=preset.max_per_seed,
        max_per_prefix=preset.max_per_prefix,
        max_per_root=preset.max_per_root,
    )
    save_keywords(enriched, output_path)

    print(f"{len(enriched)} keywords sauvegardés dans {output_path}")
    return len(enriched), output_path


if __name__ == "__main__":
    from gui import main as gui_main

    gui_main()
