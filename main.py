#!/usr/bin/env python3
import sys
import time
from pathlib import Path

import requests

from config import DEFAULT_PRESET_ID, QualityPreset, get_preset

AUTOCOMPLETE_URL = "https://suggestqueries.google.com/complete/search"
DEFAULT_DELAY = 0.12
MIN_WORDS = 1
MAX_WORDS = 3
MAX_PER_PREFIX = 3
MAX_PER_ROOT = 2
MAX_PER_SEED = 25

CURATED_MODIFIERS = [
    "gratuit", "vostfr", "vf", "streaming", "legal", "complet", "voir", "regarder",
    "site", "liste", "top", "meilleur", "forum", "avis", "prix", "guide",
    "saison", "episode", "film", "nouveau", "populaire", "culte",
    "netflix", "crunchyroll", "adn", "wakanim", "figurine", "cosplay",
    "opening", "scan", "france", "francais", "telecharger", "sans", "pub",
]

GENERIC_WORDS = frozenset({
    "abonnement", "streaming", "catalogue", "application", "plateforme",
    "regarder", "voir", "meilleur", "meilleure", "top", "nouveau", "nouveaux",
    "nouvelle", "site", "prix", "avis", "guide", "liste", "gratuit", "gratuite",
    "legal", "légal", "légale", "complet", "complète", "recent", "récent",
    "récents", "populaire", "populaires", "tendance", "culte", "mobile",
    "tablette", "smarttv", "illimité", "illimite", "télécharger", "telecharger",
    "disponible", "critique", "classement", "calendrier", "saison", "episode",
    "épisode", "serie", "série", "film", "industrie", "marche", "marché",
    "fandom", "convention", "communauté", "communaute", "fan", "playlist",
    "boutique", "acheter", "achat", "edition", "édition", "limitée", "limitee",
    "sortie", "prochaine", "renouvellement", "licence", "adaptation", "resume",
    "résumé", "fin", "explication", "personnage", "prefere", "préféré", "heros",
    "héros", "heroines", "héroïne", "antihéros", "bande", "son", "musique",
    "generique", "générique", "salon", "vpn", "sans", "publicité", "publicite",
    "hors", "ligne", "etranger", "étranger", "en", "de", "du", "la", "le", "les",
    "un", "une", "des", "pour", "avec", "sur", "par", "et", "ou", "the", "about",
    "all", "live", "news", "video", "papier", "digital", "pc", "groupé", "groupe",
    "musique", "tv", "box", "free", "base", "dernier", "dernière", "meilleure",
    "qualité", "qualite", "disponible", "france", "belgique", "légal", "offre",
    "offres", "comparer", "comparaison", "test", "forum", "avis", "reduction",
    "réduction", "promo", "code", "coupon", "gratuitement", "illimité", "pub",
})

AMBIGUOUS_WORDS = frozenset({
    "adn", "vf", "ova", "hac", "iam", "rtm", "rcv", "rds", "tec", "ter", "tcl",
    "gsm", "psn", "ugc", "ubb", "zou", "voo", "wow", "arn", "apk", "logo", "kit",
    "gym", "hair", "immo", "moto", "auto", "autos", "golf", "cycle", "danse",
    "data", "dijon", "lyon", "nord", "fajr", "juif", "kids", "klm", "kiwi",
    "musc", "box", "hey", "iam", "inwi", "edf", "eau", "gaz", "sfr", "free",
    "hbo", "psg", "vin", "zoo", "asse", "jims", "hac", "med", "rca", "ubb",
})

ENGLISH_NOISE = frozenset({
    "about", "american", "legit", "ape", "ark", "adventures", "figures", "meme",
    "tab", "girl", "boy", "zone", "queen", "line", "skeleton", "triggers",
    "paranormal", "psycho", "asylum", "bones", "law", "nintendo", "supernatural",
    "survival", "buu", "dio", "ian", "jio", "tab", "legit", "arab", "nickelodeon",
    "nyc", "pfp", "xyz", "iptv", "xbox", "pes", "css", "sites", "websites", "watch",
    "cash", "boxe", "foot", "computer", "virus", "boston", "download", "wiki",
    "platform", "application", "calendar", "community", "convention", "catalog",
})

PLATFORM_WORDS = frozenset({
    "adn", "crunchyroll", "wakanim", "funimation", "hidive", "netflix",
})

CORE_THEME_ANCHORS = frozenset({
    "anime", "manga", "vostfr", "isekai", "shonen", "seinen", "mecha", "yaoi", "yuri",
    "cosplay", "otaku", "webtoon", "simulcast", "crunchyroll", "wakanim", "funimation",
    "hidive", "fansub", "scantrad", "doujin", "kawaii", "chibi", "harem", "ecchi",
    "mangaka", "seiyu", "figurine", "goodies", "poster", "artbook", "peluche",
    "sticker", "coffret", "netflix", "kyoani", "ghibli", "mappa", "ufotable", "madhouse",
    "trigger", "bones", "toei", "opening", "ending", "tankobon", "doujin", "otaku",
    "light", "novel", "webtoon", "simulcast", "scantrad", "wakanim", "funimation",
})

BROAD_THEME_WORDS = frozenset({
    "sport", "action", "aventure", "romance", "horreur", "comédie", "comedie", "drame",
    "fantasy", "thriller", "survie", "historique", "psychologique", "surnaturel",
    "cyberpunk", "school", "life", "gore", "video", "animation", "studio", "studios",
    "streaming", "retro", "alternative", "sites", "regarder", "upcoming", "adventure",
    "anglais", "français", "francais", "francaise", "française", "prime", "sous",
    "titres", "doublage", "voix", "disponible", "france", "belgique", "mobile",
    "application", "plateforme", "catalogue", "calendrier", "classement", "critique",
    "guide", "liste", "avis", "prix", "gratuit", "legal", "légal", "complet",
    "recent", "récent", "populaire", "tendance", "culte", "nouveau", "meilleur",
})


def build_theme_vocab(seeds: list[str]) -> set[str]:
    vocab: set[str] = set()
    for seed in seeds:
        for word in seed.replace("-", " ").split():
            w = word.lower()
            if w in GENERIC_WORDS or w in AMBIGUOUS_WORDS:
                continue
            if len(w) >= 3:
                vocab.add(w)
    return vocab


def build_theme_anchors(seeds: list[str]) -> set[str]:
    anchors = set(CORE_THEME_ANCHORS)
    for seed in seeds:
        words = seed.replace("-", " ").split()
        if not ({"anime", "manga"} & set(words)):
            continue
        for w in words:
            wl = w.lower()
            if wl in GENERIC_WORDS or wl in AMBIGUOUS_WORDS or wl in BROAD_THEME_WORDS:
                continue
            if wl in {"anime", "manga"}:
                continue
            if len(wl) >= 6:
                anchors.add(wl)
    return anchors


def seed_specific_words(seed: str) -> list[str]:
    return [
        w for w in seed.split()
        if w not in GENERIC_WORDS
        and w not in AMBIGUOUS_WORDS
        and w not in BROAD_THEME_WORDS
    ]


def should_expand(seed: str) -> bool:
    specific = seed_specific_words(seed)
    if not specific:
        return False
    if len(specific) >= 2:
        return True
    return len(specific[0]) >= 4


def modifiers_for_seed(seed: str) -> list[str]:
    seed_words = set(seed.split())
    return [mod for mod in CURATED_MODIFIERS if mod not in seed_words]


def has_off_topic_tail(
    keyword: str,
    theme_vocab: set[str],
    theme_anchors: set[str] | None = None,
) -> bool:
    theme_anchors = theme_anchors or set()
    words = keyword.split()
    if len(words) <= 1:
        return False

    tail = words[1:]
    if any(w in ENGLISH_NOISE or w in AMBIGUOUS_WORDS for w in tail):
        return True

    for w in tail:
        if w in theme_anchors:
            continue
        if w in theme_vocab and w not in BROAD_THEME_WORDS:
            continue
        if len(w) <= 3:
            return True

    return False


def is_on_theme(
    keyword: str,
    seed: str,
    theme_vocab: set[str],
    theme_anchors: set[str],
    direct: set[str] | None = None,
) -> bool:
    direct = direct or set()
    words = keyword.split()
    seed_words = set(seed.split())
    word_set = set(words)

    if not seed_words.intersection(word_set):
        return False

    anchor_in_keyword = word_set & theme_anchors
    specific_seed = seed_specific_words(seed)

    platform_in_seed = seed_words & PLATFORM_WORDS
    if platform_in_seed and len(seed_words) >= 2:
        if platform_in_seed.intersection(words) and seed_words.issubset(words):
            if not has_off_topic_tail(keyword, theme_vocab, theme_anchors):
                return True

    if len(specific_seed) >= 2:
        if not all(w in words for w in specific_seed):
            return False
        return not has_off_topic_tail(keyword, theme_vocab, theme_anchors)

    if len(specific_seed) == 1:
        anchor = specific_seed[0]
        if anchor not in words:
            return False
        if has_off_topic_tail(keyword, theme_vocab, theme_anchors):
            return False
        return True

    if not anchor_in_keyword:
        return False

    if keyword in direct and anchor_in_keyword:
        return True

    return bool(anchor_in_keyword) and not has_off_topic_tail(
        keyword, theme_vocab, theme_anchors
    )


def is_valid_keyword(
    keyword: str,
    seed: str = "",
    theme_vocab: set[str] | None = None,
    theme_anchors: set[str] | None = None,
    direct: set[str] | None = None,
) -> bool:
    words = keyword.split()
    direct = direct or set()
    theme_vocab = theme_vocab or set()
    theme_anchors = theme_anchors or set()

    if not (MIN_WORDS <= len(words) <= MAX_WORDS):
        return False

    if any(char.isdigit() for char in keyword):
        return False

    if any(c in keyword for c in ".,;:"):
        return False

    if len(words) != len(set(words)):
        return False

    if len(words[-1]) <= 2 and keyword not in direct:
        return False

    if seed and theme_vocab is not None:
        if not is_on_theme(keyword, seed, theme_vocab, theme_anchors, direct):
            return False

    return True


def prefix_key(keyword: str) -> str:
    words = keyword.split()
    specific = [w for w in words if w not in GENERIC_WORDS]
    if len(specific) >= 2:
        return " ".join(specific[:2])
    if specific:
        return specific[0]
    if len(words) >= 2:
        return " ".join(words[:2])
    return words[0]


def root_key(keyword: str) -> str:
    words = keyword.split()
    specific = [
        w for w in words
        if w not in GENERIC_WORDS and w not in AMBIGUOUS_WORDS
    ]
    if not specific:
        specific = [w for w in words if w not in GENERIC_WORDS]
    if len(specific) >= 2:
        return f"{specific[0]}|{specific[-1]}"
    if specific:
        return specific[0]
    return words[0]


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


def global_dedupe(
    keywords: set[str],
    direct: set[str] | None = None,
    max_per_root: int = MAX_PER_ROOT,
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
        key = root_key(keyword)
        if buckets.get(key, 0) >= max_per_root:
            continue
        buckets[key] = buckets.get(key, 0) + 1
        kept.add(keyword)

    return kept


def filter_keywords(
    raw_keywords: set[str],
    seed: str,
    theme_vocab: set[str],
    theme_anchors: set[str],
    direct: set[str],
    max_per_seed: int = MAX_PER_SEED,
    max_per_prefix: int = MAX_PER_PREFIX,
) -> set[str]:
    valid = {
        kw for kw in raw_keywords
        if is_valid_keyword(
            kw,
            seed=seed,
            theme_vocab=theme_vocab,
            theme_anchors=theme_anchors,
            direct=direct,
        )
    }
    deduped = dedupe_repetitive(valid, direct=direct, max_per_prefix=max_per_prefix)

    if len(deduped) <= max_per_seed:
        return deduped

    def rank(keyword: str) -> tuple:
        return (
            0 if keyword in direct else 1,
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
    params = {"client": "firefox", "hl": lang, "q": query}
    response = requests.get(
        AUTOCOMPLETE_URL,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list) or len(data) < 2:
        return []
    return [s.lower() for s in data[1] if isinstance(s, str)]


def build_queries(seed: str) -> list[str]:
    queries = [seed]
    if should_expand(seed):
        queries.extend(f"{seed} {mod}" for mod in modifiers_for_seed(seed))
    return queries


def expand_keyword(seed: str, lang: str, delay: float) -> tuple[set[str], set[str]]:
    results: set[str] = set()
    direct: set[str] = set()

    for query in build_queries(seed):
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
    lang: str = "fr",
    delay: float = DEFAULT_DELAY,
    max_per_seed: int = MAX_PER_SEED,
    max_per_prefix: int = MAX_PER_PREFIX,
    max_per_root: int = MAX_PER_ROOT,
) -> set[str]:
    theme_vocab = build_theme_vocab(input_keywords)
    theme_anchors = build_theme_anchors(input_keywords)
    all_keywords: set[str] = set()
    all_direct: set[str] = set()
    total_raw = 0
    total_filtered = 0

    print(
        f"Source : Google autocomplete | filtre thème intelligent\n"
        f"Limites : {max_per_seed}/seed, {max_per_prefix}/préfixe, {max_per_root}/racine\n"
        f"Vocabulaire thème : {len(theme_vocab)} mots, {len(theme_anchors)} ancres\n"
    )

    for index, seed in enumerate(input_keywords, start=1):
        print(f"[{index}/{len(input_keywords)}] {seed}")
        expanded, direct = expand_keyword(seed, lang, delay)
        total_raw += len(expanded)
        all_direct.update(direct)

        cleaned = filter_keywords(
            expanded,
            seed=seed,
            theme_vocab=theme_vocab,
            theme_anchors=theme_anchors,
            direct=direct,
            max_per_seed=max_per_seed,
            max_per_prefix=max_per_prefix,
        )
        total_filtered += len(cleaned)
        all_keywords.update(cleaned)

        mode = "direct" if not should_expand(seed) else f"{len(build_queries(seed))} requêtes"
        print(
            f"  => {len(expanded)} brutes -> {len(cleaned)} retenues "
            f"({mode}, {len(all_keywords)} uniques au total)\n"
        )

    before_global = len(all_keywords)
    all_keywords = global_dedupe(all_keywords, direct=all_direct, max_per_root=max_per_root)

    print(
        f"Filtrage : {total_raw} brutes -> {total_filtered} retenues "
        f"-> {before_global} uniques -> {len(all_keywords)} après dédup globale "
        f"(max {max_per_prefix}/préfixe, max {max_per_root}/racine)\n"
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
    lang: str = "fr",
    delay: float = DEFAULT_DELAY,
    preset_id: str = DEFAULT_PRESET_ID,
) -> tuple[int, Path]:
    if output_path is None:
        output_path = input_path.with_name(f"{input_path.stem}_keywords.txt")

    preset = get_preset(preset_id)
    input_keywords = load_keywords(input_path)
    print(f"{len(input_keywords)} keywords chargés depuis {input_path}")
    print(f"Preset : {preset.label}\n")

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
