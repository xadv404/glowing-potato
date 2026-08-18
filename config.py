from dataclasses import dataclass


@dataclass(frozen=True)
class QualityPreset:
    id: str
    label: str
    description: str
    max_per_seed: int
    max_per_prefix: int
    max_per_root: int


@dataclass(frozen=True)
class LanguageProfile:
    code: str
    label: str
    stopwords: frozenset[str]


QUALITY_PRESETS: dict[str, QualityPreset] = {
    "strict": QualityPreset(
        id="strict",
        label="Strict (HQ)",
        description=(
            "Peu de keywords par seed, dédup forte. "
            "Idéal pour listes ciblées."
        ),
        max_per_seed=15,
        max_per_prefix=2,
        max_per_root=1,
    ),
    "balanced": QualityPreset(
        id="balanced",
        label="Équilibré (recommandé)",
        description=(
            "Bon compromis qualité / volume. "
            "Filtrage thème dynamique basé sur les seeds."
        ),
        max_per_seed=25,
        max_per_prefix=3,
        max_per_root=2,
    ),
    "permissive": QualityPreset(
        id="permissive",
        label="Permissif",
        description=(
            "Plus de keywords retenus par seed."
        ),
        max_per_seed=35,
        max_per_prefix=4,
        max_per_root=2,
    ),
    "volume": QualityPreset(
        id="volume",
        label="Volume max",
        description=(
            "Limites assouplies pour enrichir de grosses listes de seeds."
        ),
        max_per_seed=45,
        max_per_prefix=5,
        max_per_root=3,
    ),
}

DEFAULT_PRESET_ID = "balanced"
DEFAULT_LANG = "fr"

SCORE_PRESETS = QUALITY_PRESETS  # alias compat

CASELESS_LANGS = frozenset({"ja", "ko", "zh", "zh-cn", "zh-tw", "zh-hk"})


class UnsupportedLanguageError(ValueError):
    def __init__(self, lang: str) -> None:
        self.lang = lang
        codes = ", ".join(profile.code for profile in LANGUAGE_PROFILES.values())
        super().__init__(
            f"Langue « {lang} » non maîtrisée.\n"
            f"Nous ne disposons pas de stopwords pour cette langue.\n"
            f"Langues supportées : {codes}"
        )


# Stopwords linguistiques uniquement (articles, prépositions, pronoms).
# Aucun terme de niche — tout le vocabulaire thématique vient des seeds.

LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "fr": LanguageProfile(
        code="fr",
        label="Français",
        stopwords=frozenset({
            "le", "la", "les", "l", "un", "une", "des", "de", "du", "d",
            "en", "au", "aux", "et", "ou", "pour", "avec", "sur", "par",
            "dans", "sans", "sous", "vers", "ce", "se", "sa", "son", "ses",
            "mon", "ma", "mes", "ton", "ta", "tes", "qui", "que", "qu",
            "ne", "pas", "plus", "très", "bien", "tout", "tous",
        }),
    ),
    "en": LanguageProfile(
        code="en",
        label="English",
        stopwords=frozenset({
            "the", "a", "an", "of", "in", "on", "at", "to", "for", "with",
            "and", "or", "by", "from", "is", "it", "this", "that", "are",
            "be", "as", "not", "but", "was", "all", "we", "my", "your",
            "our", "their", "no", "do", "how", "what", "which",
        }),
    ),
    "es": LanguageProfile(
        code="es",
        label="Español",
        stopwords=frozenset({
            "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
            "en", "al", "y", "o", "para", "con", "por", "sin", "se", "su",
            "sus", "mi", "tu", "que", "no", "es", "son", "fue",
        }),
    ),
    "de": LanguageProfile(
        code="de",
        label="Deutsch",
        stopwords=frozenset({
            "der", "die", "das", "des", "dem", "den", "ein", "eine", "einen",
            "und", "oder", "für", "von", "mit", "bei", "nach", "aus", "an",
            "in", "auf", "ist", "sind", "war", "nicht", "ich", "sie", "er",
            "es", "wir", "ihr", "mein", "dein", "sein",
        }),
    ),
    "pt": LanguageProfile(
        code="pt",
        label="Português",
        stopwords=frozenset({
            "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas", "ao", "aos", "e", "ou", "para",
            "com", "por", "sem", "se", "sua", "seu", "que", "não", "mais",
        }),
    ),
    "it": LanguageProfile(
        code="it",
        label="Italiano",
        stopwords=frozenset({
            "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "del",
            "della", "dei", "degli", "delle", "in", "nel", "nella", "su", "sul",
            "sulla", "e", "o", "per", "con", "ma", "non", "che", "si", "è",
        }),
    ),
    "ja": LanguageProfile(
        code="ja",
        label="日本語",
        stopwords=frozenset(),
    ),
    "ko": LanguageProfile(
        code="ko",
        label="한국어",
        stopwords=frozenset(),
    ),
    "zh-cn": LanguageProfile(
        code="zh-CN",
        label="中文 (简体)",
        stopwords=frozenset(),
    ),
    "zh-tw": LanguageProfile(
        code="zh-TW",
        label="中文 (繁體)",
        stopwords=frozenset(),
    ),
    "ru": LanguageProfile(
        code="ru",
        label="Русский",
        stopwords=frozenset({
            "и", "в", "не", "на", "с", "из", "по", "это", "для", "он", "она",
            "они", "мы", "я", "ты", "что", "как", "все", "от", "за", "при",
            "но", "или", "то", "же", "так", "уже", "до", "со",
        }),
    ),
    "ar": LanguageProfile(
        code="ar",
        label="العربية",
        stopwords=frozenset({
            "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "التي", "الذي",
            "و", "أو", "لا", "ما", "كان", "كل", "هو", "هي", "أن", "بعد",
        }),
    ),
    "nl": LanguageProfile(
        code="nl",
        label="Nederlands",
        stopwords=frozenset({
            "de", "het", "een", "van", "in", "op", "aan", "met", "voor", "bij",
            "en", "of", "maar", "niet", "dat", "dit", "zijn", "was", "ze", "hij",
        }),
    ),
    "pl": LanguageProfile(
        code="pl",
        label="Polski",
        stopwords=frozenset({
            "i", "w", "z", "na", "do", "to", "się", "że", "nie", "jak",
            "o", "ale", "po", "za", "przy", "tak", "dla", "jest", "przez",
        }),
    ),
    "tr": LanguageProfile(
        code="tr",
        label="Türkçe",
        stopwords=frozenset({
            "ve", "bir", "bu", "de", "da", "ile", "için", "gibi", "kadar",
            "ama", "ya", "ne", "ben", "sen", "biz", "siz", "çok", "daha",
        }),
    ),
}

LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    (profile.code, profile.label) for profile in LANGUAGE_PROFILES.values()
]


def normalize_lang(code: str) -> str:
    normalized = code.strip().lower().replace("_", "-")
    if normalized in LANGUAGE_PROFILES:
        return normalized
    if normalized.startswith("zh"):
        if "tw" in normalized or "hk" in normalized or "hant" in normalized:
            return "zh-tw"
        return "zh-cn"
    if normalized.startswith("pt"):
        return "pt"
    base = normalized.split("-")[0]
    if base in LANGUAGE_PROFILES:
        return base
    return normalized


def is_supported_lang(lang: str) -> bool:
    return normalize_lang(lang) in LANGUAGE_PROFILES


def get_lang_profile(lang: str) -> LanguageProfile:
    key = normalize_lang(lang)
    if key in LANGUAGE_PROFILES:
        return LANGUAGE_PROFILES[key]
    raise UnsupportedLanguageError(lang.strip())


def get_google_hl(lang: str) -> str:
    return get_lang_profile(lang).code


def get_preset(preset_id: str) -> QualityPreset:
    return QUALITY_PRESETS.get(preset_id, QUALITY_PRESETS[DEFAULT_PRESET_ID])
