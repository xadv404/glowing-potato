#!/usr/bin/env python3
import sys
import time
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
DEFAULT_DELAY = 0.12
MIN_WORDS = 1
MAX_WORDS = 3
MAX_PER_PREFIX = 3
MAX_PER_ROOT = 2
MAX_PER_SEED = 25

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
    # EN / autres langues
    "watch", "stream", "online", "download", "best", "list", "review", "price",
    "season", "episode", "movie", "series", "complete", "popular", "new", "full",
    "gratis", "ver", "kostenlos", "kijken", "vedere", "izle", "ucretsiz", "ücretsiz",
})

AMBIGUOUS_WORDS = frozenset({
    "vf", "ova", "canon", "filler", "hac", "iam", "rtm", "rcv", "rds", "tec", "ter", "tcl",
    "gsm", "psn", "ugc", "ubb", "zou", "voo", "wow", "arn", "apk", "logo", "kit",
    "gym", "hair", "immo", "moto", "auto", "autos", "golf", "cycle", "danse",
    "data", "dijon", "lyon", "nord", "fajr", "juif", "kids", "klm", "kiwi",
    "musc", "box", "hey", "iam", "inwi", "edf", "eau", "gaz", "sfr", "free",
    "hbo", "psg", "vin", "zoo", "asse", "jims", "hac", "med", "rca", "ubb",
})

# Pollution EN quand hl ≠ en
ENGLISH_NOISE = frozenset({
    "about", "american", "legit", "ape", "ark", "figures", "meme",
    "tab", "girl", "boy", "zone", "queen", "line", "skeleton", "triggers",
    "paranormal", "psycho", "asylum", "bones", "law", "nintendo", "supernatural",
    "survival", "buu", "dio", "ian", "jio", "tab", "legit", "arab", "nickelodeon",
    "nyc", "pfp", "xyz", "iptv", "xbox", "pes", "css", "sites", "websites", "watch",
    "cash", "boxe", "foot", "computer", "virus", "boston", "download", "wiki",
    "platform", "application", "calendar", "community", "convention", "catalog",
})

ENGLISH_TAIL_WORDS = frozenset({
    "adventure", "comedy", "popular", "complete", "series", "cultural", "impact",
    "influence", "references", "catalogs", "service", "collection", "videos",
    "couple", "commune", "dramedy", "dungeons", "expeditions", "guidelines",
    "guideau", "guideverse", "puberty", "completo", "plattform", "filme", "maiwenn",
    "stremio", "catalog", "community", "calendar", "typing", "tower", "style",
    "best", "list", "game", "tips", "codes", "popular", "season", "episode",
    "american", "influence", "references", "culture", "impact", "series",
    "complete", "guideline", "guidelines", "video", "videos", "couple",
    "commune", "service", "collection", "catalogs", "catalog", "dramedy",
    "dungeons", "expeditions", "apocalypse", "skeleton", "triggers", "school",
})

OFF_TOPIC_WORDS = frozenset({
    "codes", "code", "guideau", "guideverse", "maiwenn", "plattform", "filme",
    "completo", "stremio", "expeditions", "dramedy", "guidelines", "puberty",
    "nexus", "salt", "sama", "slayer", "wallpaper", "recap", "horizon",
})

# Jargon anime pollué seul dans l'autocomplete (canon=appareil photo, filler=médecine…).
AMBIGUOUS_JARGON = frozenset({
    "canon", "filler", "ending", "opening", "spinoff", "ova", "vf",
    "reboot", "remaster", "binge-watching", "light-novel",
})

# Contexte anime/manga obligatoire si jargon ambigu présent sans seed multi-mot contextualisé.
ANIME_CONTEXT_WORDS = frozenset({
    "anime", "manga", "vostfr", "isekai", "shonen", "seinen", "mecha",
    "yaoi", "yuri", "scantrad", "fansub", "simulcast", "webtoon", "doujin",
    "アニメ", "マンガ", "动漫", "动画", "動漫", "動畫", "аниме", "манга",
})

# Mots seuls trop génériques / pollués pour être retenus sans autre ancrage.
WEAK_STANDALONE_WORDS = AMBIGUOUS_JARGON | frozenset({
    "fansub", "scantrad", "simulcast", "doujin", "tankobon", "otaku", "webtoon",
    "gore", "ecchi", "harem", "streaming",
})

# Pollution domaines hors anime (photo, médical, tech, jeux…).
POLLUTION_WORDS = frozenset({
    "camera", "imprimante", "printer", "printers", "pixma", "powershot", "scanner",
    "scanners", "argentique", "dermal", "abdominal", "docteur", "medical", "medecin",
    "gamefaqs", "pubg", "subscription", "subscriptions", "drivers", "driver",
    "utilities", "testament", "simulation", "definition", "office", "scandal",
    "game", "games", "body", "chin", "parallel", "broken", "adnan", "adnil",
    "comedy", "computer", "community", "catalog", "collection", "subscription",
})

PLATFORM_WORDS = frozenset({
    "adn", "crunchyroll", "wakanim", "funimation", "hidive", "netflix",
})

# Plateformes courtes : autocomplete Google produit adnan/adnil pour le seed « adn ».
SHORT_PLATFORM_MAX_LEN = 4

CORE_THEME_ANCHORS = frozenset({
    "anime", "manga", "vostfr", "adn", "isekai", "shonen", "seinen", "mecha", "yaoi", "yuri",
    "cosplay", "otaku", "webtoon", "simulcast", "crunchyroll", "wakanim", "funimation",
    "hidive", "fansub", "scantrad", "doujin", "kawaii", "chibi", "harem", "ecchi",
    "mangaka", "seiyu", "figurine", "goodies", "poster", "artbook", "peluche",
    "sticker", "coffret", "netflix", "kyoani", "ghibli", "mappa", "ufotable", "madhouse",
    "trigger", "bones", "toei", "tankobon", "light", "novel",
    "アニメ", "マンガ", "漫画", "애니", "애니메", "만화", "动漫", "动画", "動漫", "動畫",
    "аниме", "манга",
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
    "comedy", "horror", "drama", "watch", "stream", "online", "free", "complete",
})

CJK_RANGES = (
    (0x3040, 0x30FF),  # Hiragana + Katakana
    (0x4E00, 0x9FFF),  # CJK Unified
    (0xAC00, 0xD7AF),  # Hangul
)


def is_cjk_lang(lang: str) -> bool:
    return normalize_lang(lang) in CASELESS_LANGS or normalize_lang(lang).startswith("zh")


def normalize_keyword(text: str, lang: str) -> str:
    if is_cjk_lang(lang):
        return text.strip()
    return text.strip().lower()


def has_cjk_chars(text: str) -> bool:
    for char in text:
        code = ord(char)
        for start, end in CJK_RANGES:
            if start <= code <= end:
                return True
    return False


def is_platform_prefix_false_positive(word: str) -> bool:
    """Rejette adnan/adnil… : mots qui commencent par une plateforme sans être celle-ci."""
    wl = word.lower()
    for platform in PLATFORM_WORDS:
        plen = len(platform)
        if plen <= SHORT_PLATFORM_MAX_LEN and wl.startswith(platform) and wl != platform:
            if len(wl) > plen:
                return True
    return False


def seed_has_anime_context(seed: str, lang: str = DEFAULT_LANG) -> bool:
    words = set(normalize_keyword(seed, lang).replace("-", " ").split())
    return bool(words & ANIME_CONTEXT_WORDS)


def keyword_has_anime_context(keyword: str) -> bool:
    words = set(keyword.replace("-", " ").split())
    return bool(words & ANIME_CONTEXT_WORDS)


def contains_ambiguous_jargon(keyword: str) -> bool:
    words = set(keyword.replace("-", " ").split())
    return bool(words & AMBIGUOUS_JARGON)


def is_ambiguous_jargon_only_seed(seed: str, lang: str = DEFAULT_LANG) -> bool:
    words = normalize_keyword(seed, lang).replace("-", " ").split()
    specific = seed_specific_words(seed, lang)
    return len(words) == 1 and len(specific) == 1 and specific[0] in AMBIGUOUS_JARGON


def has_pollution(keyword: str) -> bool:
    words = keyword.replace("-", " ").split()
    for w in words:
        wl = w.lower()
        if wl in POLLUTION_WORDS:
            return True
        if wl in OFF_TOPIC_WORDS:
            return True
    return False


def requires_explicit_anime_context(keyword: str, seed: str, lang: str = DEFAULT_LANG) -> bool:
    """Jargon ambigu sans contexte anime dans le seed → exiger anime/manga dans le keyword."""
    if not contains_ambiguous_jargon(keyword):
        return False
    return not seed_has_anime_context(seed, lang)


def build_theme_vocab(seeds: list[str], lang: str = DEFAULT_LANG) -> set[str]:
    vocab: set[str] = set()
    for seed in seeds:
        normalized = normalize_keyword(seed, lang)
        for word in normalized.replace("-", " ").split():
            w = word.lower() if not is_cjk_lang(lang) else word
            if w in GENERIC_WORDS or w in AMBIGUOUS_WORDS:
                continue
            if len(w) >= 2 if is_cjk_lang(lang) else len(w) >= 3:
                vocab.add(w)
    return vocab


def build_theme_anchors(seeds: list[str], lang: str = DEFAULT_LANG) -> set[str]:
    anchors = set(CORE_THEME_ANCHORS)
    for seed in seeds:
        normalized = normalize_keyword(seed, lang)
        words = normalized.replace("-", " ").split()
        word_set = {w.lower() if not is_cjk_lang(lang) else w for w in words}
        if not ({"anime", "manga", "アニメ", "マンガ", "애니", "动漫", "動漫"} & word_set):
            continue
        for w in words:
            wl = w.lower() if not is_cjk_lang(lang) else w
            if wl in GENERIC_WORDS or wl in AMBIGUOUS_WORDS or wl in BROAD_THEME_WORDS:
                continue
            if wl in {"anime", "manga", "アニメ", "マンガ", "애니", "动漫", "動漫"}:
                continue
            min_len = 2 if is_cjk_lang(lang) else 6
            if len(wl) >= min_len:
                anchors.add(wl)
    return anchors


def seed_specific_words(seed: str, lang: str = DEFAULT_LANG) -> list[str]:
    normalized = normalize_keyword(seed, lang)
    return [
        w for w in normalized.split()
        if w not in GENERIC_WORDS
        and w not in AMBIGUOUS_WORDS
        and w not in BROAD_THEME_WORDS
    ]


def should_expand(seed: str, lang: str = DEFAULT_LANG) -> bool:
    if is_ambiguous_jargon_only_seed(seed, lang):
        return False
    specific = seed_specific_words(seed, lang)
    if not specific:
        return False
    if len(specific) >= 2:
        return True
    min_len = 2 if is_cjk_lang(lang) else 4
    if specific[0] in AMBIGUOUS_JARGON:
        return False
    return len(specific[0]) >= min_len


def modifiers_for_seed(seed: str, lang: str = DEFAULT_LANG) -> list[str]:
    profile = get_lang_profile(lang)
    seed_words = set(normalize_keyword(seed, lang).split())
    return [mod for mod in profile.modifiers if mod not in seed_words]


def has_native_marker(word: str, profile: LanguageProfile) -> bool:
    if has_cjk_chars(word):
        return True
    if profile.native_chars and any(c in word for c in profile.native_chars):
        return True
    if profile.native_suffixes:
        wl = word.lower()
        return any(wl.endswith(suffix) for suffix in profile.native_suffixes)
    return False


def is_acceptable_word(
    word: str,
    theme_vocab: set[str],
    theme_anchors: set[str],
    profile: LanguageProfile,
) -> bool:
    wl = word.lower() if not has_cjk_chars(word) else word
    if wl in theme_anchors or wl in CORE_THEME_ANCHORS:
        return True
    if wl in profile.acceptable_words:
        return True
    if wl in theme_vocab and wl not in BROAD_THEME_WORDS:
        return True
    if has_native_marker(word, profile) and len(word) >= 3:
        return True
    return False


def has_off_topic_tail(
    keyword: str,
    theme_vocab: set[str],
    theme_anchors: set[str] | None,
    profile: LanguageProfile,
) -> bool:
    theme_anchors = theme_anchors or set()
    words = keyword.split()
    if len(words) <= 1:
        return False

    tail = words[1:]

    if keyword_has_anime_context(keyword):
        for w in tail:
            wl = w.lower()
            if wl in POLLUTION_WORDS or wl in OFF_TOPIC_WORDS:
                return True
            if profile.block_english_pollution and (
                wl in ENGLISH_NOISE or wl in ENGLISH_TAIL_WORDS
            ):
                return True
        return False

    blocked = OFF_TOPIC_WORDS | AMBIGUOUS_WORDS | POLLUTION_WORDS
    if profile.block_english_pollution:
        blocked = blocked | ENGLISH_NOISE | ENGLISH_TAIL_WORDS

    if any(w in blocked or w.lower() in blocked for w in tail):
        return True

    for w in tail:
        if w.lower() in AMBIGUOUS_JARGON:
            return True
        if is_acceptable_word(w, theme_vocab, theme_anchors, profile):
            continue
        if has_cjk_chars(w):
            continue
        if len(w) <= 3:
            return True
        if len(w) >= 4 and not has_native_marker(w, profile):
            if profile.block_english_pollution:
                return True

    return False


def keyword_has_theme_anchor(
    keyword: str,
    theme_vocab: set[str],
    theme_anchors: set[str],
    lang: str = DEFAULT_LANG,
) -> bool:
    words = set(keyword.split())
    if words & theme_anchors:
        return True
    specific = {
        w for w in words
        if w in theme_vocab and w not in GENERIC_WORDS and w not in BROAD_THEME_WORDS
    }
    if is_cjk_lang(lang) and len(specific) >= 1:
        return True
    return len(specific) >= 1


def is_on_theme(
    keyword: str,
    seed: str,
    theme_vocab: set[str],
    theme_anchors: set[str],
    profile: LanguageProfile,
    direct: set[str] | None = None,
    lang: str = DEFAULT_LANG,
) -> bool:
    direct = direct or set()
    words = keyword.split()
    seed_words = set(normalize_keyword(seed, lang).split())
    word_set = set(words)

    if not seed_words.intersection(word_set):
        # Pour CJK : comparer aussi en minuscules si seed latin
        if not is_cjk_lang(lang):
            return False
        seed_lower = {w.lower() for w in seed_words}
        word_lower = {w.lower() for w in word_set}
        if not seed_lower.intersection(word_lower):
            return False

    anchor_in_keyword = word_set & theme_anchors
    specific_seed = seed_specific_words(seed, lang)

    platform_in_seed = seed_words & PLATFORM_WORDS
    if platform_in_seed and len(seed_words) >= 2:
        if platform_in_seed.intersection(words) and seed_words.issubset(words):
            if not has_off_topic_tail(keyword, theme_vocab, theme_anchors, profile):
                return True

    if len(specific_seed) >= 2:
        if not all(w in words for w in specific_seed):
            return False
        return not has_off_topic_tail(keyword, theme_vocab, theme_anchors, profile)

    if len(specific_seed) == 1:
        anchor = specific_seed[0]
        if anchor not in words:
            return False
        if has_off_topic_tail(keyword, theme_vocab, theme_anchors, profile):
            return False
        return True

    if not anchor_in_keyword:
        return False

    if keyword in direct and anchor_in_keyword:
        return True

    return bool(anchor_in_keyword) and not has_off_topic_tail(
        keyword, theme_vocab, theme_anchors, profile
    )


def is_valid_keyword(
    keyword: str,
    seed: str = "",
    theme_vocab: set[str] | None = None,
    theme_anchors: set[str] | None = None,
    direct: set[str] | None = None,
    profile: LanguageProfile | None = None,
    lang: str = DEFAULT_LANG,
) -> bool:
    words = keyword.split()
    direct = direct or set()
    theme_vocab = theme_vocab or set()
    theme_anchors = theme_anchors or set()
    profile = profile or get_lang_profile(lang)

    if not (MIN_WORDS <= len(words) <= MAX_WORDS):
        return False

    if any(char.isdigit() for char in keyword):
        return False

    if any(c in keyword for c in ".,;:"):
        return False

    if len(words) != len(set(words)):
        return False

    if any(is_platform_prefix_false_positive(w) for w in words):
        return False

    if has_pollution(keyword):
        return False

    if requires_explicit_anime_context(keyword, seed, lang) and not keyword_has_anime_context(keyword):
        return False

    min_tail = 1 if is_cjk_lang(lang) else 2
    if len(words[-1]) <= min_tail and keyword not in direct:
        return False

    if seed and theme_vocab is not None:
        if not is_on_theme(
            keyword, seed, theme_vocab, theme_anchors, profile, direct, lang
        ):
            return False
        if len(words) >= 2 and not keyword_has_theme_anchor(
            keyword, theme_vocab, theme_anchors, lang
        ):
            return False
        if len(words) == 1:
            wl = words[0].lower() if not has_cjk_chars(words[0]) else words[0]
            if wl in WEAK_STANDALONE_WORDS:
                return False
            if wl not in theme_anchors and wl not in CORE_THEME_ANCHORS:
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
    profile: LanguageProfile,
    lang: str = DEFAULT_LANG,
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
            profile=profile,
            lang=lang,
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
    results = []
    for s in data[1]:
        if isinstance(s, str):
            results.append(normalize_keyword(s, lang))
    return results


def build_queries(seed: str, lang: str = DEFAULT_LANG) -> list[str]:
    queries = [seed]
    if should_expand(seed, lang):
        queries.extend(f"{seed} {mod}" for mod in modifiers_for_seed(seed, lang))
    return queries


def expand_keyword(seed: str, lang: str, delay: float) -> tuple[set[str], set[str]]:
    results: set[str] = set()
    direct: set[str] = set()

    for query in build_queries(seed, lang):
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
    theme_vocab = build_theme_vocab(input_keywords, lang)
    theme_anchors = build_theme_anchors(input_keywords, lang)
    all_keywords: set[str] = set()
    all_direct: set[str] = set()
    total_raw = 0
    total_filtered = 0

    print(
        f"Source : Google autocomplete (hl={get_google_hl(lang)}) | "
        f"langue : {profile.label}\n"
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
            profile=profile,
            lang=lang,
            max_per_seed=max_per_seed,
            max_per_prefix=max_per_prefix,
        )
        total_filtered += len(cleaned)
        all_keywords.update(cleaned)

        mode = "direct" if not should_expand(seed, lang) else f"{len(build_queries(seed, lang))} requêtes"
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
