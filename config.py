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
    generic_modifiers: tuple[str, ...]
    stopwords: frozenset[str]
    native_suffixes: tuple[str, ...]
    native_chars: frozenset[str]
    block_english_pollution: bool


QUALITY_PRESETS: dict[str, QualityPreset] = {
    "strict": QualityPreset(
        id="strict",
        label="Strict (HQ)",
        description=(
            "Peu de keywords par seed, dédup forte. "
            "Filtrage thème strict — idéal pour listes ciblées."
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
            "Autocomplete Google + filtre thème intelligent."
        ),
        max_per_seed=25,
        max_per_prefix=3,
        max_per_root=2,
    ),
    "permissive": QualityPreset(
        id="permissive",
        label="Permissif",
        description=(
            "Plus de keywords retenus par seed. "
            "Filtrage thème toujours actif."
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
            f"Nous ne disposons pas de filtrage ni de modificateurs pour cette langue.\n"
            f"Langues supportées : {codes}"
        )


_FR_STOPS = frozenset({
    "le", "la", "les", "l", "un", "une", "des", "de", "du", "d",
    "en", "au", "aux", "et", "ou", "pour", "avec", "sur", "par",
    "dans", "sans", "sous", "vers", "ce", "se", "sa", "son", "ses",
    "mon", "ma", "mes", "ton", "ta", "tes", "qui", "que", "qu",
    "ne", "pas", "plus", "très", "bien", "tout", "tous",
})

_EN_STOPS = frozenset({
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "with",
    "and", "or", "by", "from", "is", "it", "this", "that", "are",
    "be", "as", "not", "but", "was", "all", "we", "my", "your",
    "our", "their", "no", "do", "how", "what", "which",
})

_ES_STOPS = frozenset({
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "en", "al", "y", "o", "para", "con", "por", "sin", "se", "su",
    "sus", "mi", "tu", "que", "no", "es", "son", "fue",
})

_DE_STOPS = frozenset({
    "der", "die", "das", "des", "dem", "den", "ein", "eine", "einen",
    "und", "oder", "für", "von", "mit", "bei", "nach", "aus", "an",
    "in", "auf", "ist", "sind", "war", "nicht", "ich", "sie", "er",
    "es", "wir", "ihr", "mein", "dein", "sein",
})

_PT_STOPS = frozenset({
    "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "ao", "aos", "e", "ou", "para",
    "com", "por", "sem", "se", "sua", "seu", "que", "não", "mais",
})

_IT_STOPS = frozenset({
    "il", "lo", "la", "i", "gli", "le", "un", "uno", "una", "di", "del",
    "della", "dei", "degli", "delle", "in", "nel", "nella", "su", "sul",
    "sulla", "e", "o", "per", "con", "ma", "non", "che", "si", "è",
})

_RU_STOPS = frozenset({
    "и", "в", "не", "на", "с", "из", "по", "это", "для", "он", "она",
    "они", "мы", "я", "ты", "что", "как", "все", "от", "за", "при",
    "но", "или", "то", "же", "так", "уже", "до", "со",
})

_AR_STOPS = frozenset({
    "في", "من", "إلى", "على", "عن", "مع", "هذا", "هذه", "التي", "الذي",
    "و", "أو", "لا", "ما", "كان", "كل", "هو", "هي", "أن", "بعد",
})

_JA_STOPS: frozenset[str] = frozenset()
_KO_STOPS: frozenset[str] = frozenset()
_ZH_STOPS: frozenset[str] = frozenset()

_NL_STOPS = frozenset({
    "de", "het", "een", "van", "in", "op", "aan", "met", "voor", "bij",
    "en", "of", "maar", "niet", "dat", "dit", "zijn", "was", "ze", "hij",
})

_PL_STOPS = frozenset({
    "i", "w", "z", "na", "do", "to", "się", "że", "nie", "jak",
    "o", "ale", "po", "za", "przy", "tak", "dla", "jest", "przez",
})

_TR_STOPS = frozenset({
    "ve", "bir", "bu", "de", "da", "ile", "için", "gibi", "kadar",
    "ama", "ya", "ne", "ben", "sen", "biz", "siz", "çok", "daha",
})

LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "fr": LanguageProfile(
        code="fr",
        label="Français",
        generic_modifiers=(
            "gratuit", "streaming", "voir", "liste", "forum",
            "avis", "prix", "meilleur", "guide", "site",
        ),
        stopwords=_FR_STOPS,
        native_suffixes=(
            "tion", "sion", "ment", "eux", "euse", "eur", "ais", "ois", "ant", "ent",
            "age", "ique", "able", "elle", "ette", "aux", "eau",
        ),
        native_chars=frozenset("àâäéèêëïîôùûüç"),
        block_english_pollution=True,
    ),
    "en": LanguageProfile(
        code="en",
        label="English",
        generic_modifiers=(
            "free", "online", "best", "top", "list", "review",
            "guide", "site", "forum", "download",
        ),
        stopwords=_EN_STOPS,
        native_suffixes=("tion", "ness", "ment", "ing", "ous", "ful", "ive", "able", "ish"),
        native_chars=frozenset(),
        block_english_pollution=False,
    ),
    "es": LanguageProfile(
        code="es",
        label="Español",
        generic_modifiers=(
            "gratis", "ver", "streaming", "lista", "mejor",
            "guia", "foro", "precio", "online", "descargar",
        ),
        stopwords=_ES_STOPS,
        native_suffixes=("ción", "cion", "dad", "mente", "ado", "ada", "oso", "osa", "aje"),
        native_chars=frozenset("áéíóúüñ"),
        block_english_pollution=True,
    ),
    "de": LanguageProfile(
        code="de",
        label="Deutsch",
        generic_modifiers=(
            "gratis", "kostenlos", "stream", "online", "liste",
            "beste", "guide", "forum", "preis", "sehen",
        ),
        stopwords=_DE_STOPS,
        native_suffixes=("ung", "heit", "keit", "lich", "isch", "los", "bar", "ieren"),
        native_chars=frozenset("äöüß"),
        block_english_pollution=True,
    ),
    "pt": LanguageProfile(
        code="pt",
        label="Português",
        generic_modifiers=(
            "gratis", "ver", "streaming", "lista", "melhor",
            "guia", "forum", "preco", "online", "legendado",
        ),
        stopwords=_PT_STOPS,
        native_suffixes=("ção", "cao", "dade", "mente", "ado", "ada", "oso", "osa", "agem"),
        native_chars=frozenset("áâãàéêíóôõúç"),
        block_english_pollution=True,
    ),
    "it": LanguageProfile(
        code="it",
        label="Italiano",
        generic_modifiers=(
            "gratis", "gratuito", "vedere", "streaming", "lista",
            "migliore", "guida", "forum", "prezzo", "online",
        ),
        stopwords=_IT_STOPS,
        native_suffixes=("zione", "mente", "ato", "ata", "oso", "osa", "aggio", "ità", "ita"),
        native_chars=frozenset("àèéìíîòóù"),
        block_english_pollution=True,
    ),
    "ja": LanguageProfile(
        code="ja",
        label="日本語",
        generic_modifiers=(
            "無料", "配信", "視聴", "一覧", "おすすめ",
            "ランキング", "最新", "人気", "サイト", "方法",
        ),
        stopwords=_JA_STOPS,
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=False,
    ),
    "ko": LanguageProfile(
        code="ko",
        label="한국어",
        generic_modifiers=(
            "무료", "스트리밍", "시청", "온라인", "추천",
            "인기", "목록", "최신", "랭킹", "방법",
        ),
        stopwords=_KO_STOPS,
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=False,
    ),
    "zh-cn": LanguageProfile(
        code="zh-CN",
        label="中文 (简体)",
        generic_modifiers=(
            "免费", "在线", "观看", "推荐", "热门",
            "列表", "最新", "排行", "网站", "下载",
        ),
        stopwords=_ZH_STOPS,
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=False,
    ),
    "zh-tw": LanguageProfile(
        code="zh-TW",
        label="中文 (繁體)",
        generic_modifiers=(
            "免費", "線上", "觀看", "推薦", "熱門",
            "列表", "最新", "排行", "網站", "下載",
        ),
        stopwords=_ZH_STOPS,
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=False,
    ),
    "ru": LanguageProfile(
        code="ru",
        label="Русский",
        generic_modifiers=(
            "бесплатно", "онлайн", "смотреть", "список", "лучший",
            "топ", "форум", "цена", "новый", "популярный",
        ),
        stopwords=_RU_STOPS,
        native_suffixes=("ция", "ость", "ение", "ный", "ная", "ное", "ский", "ская"),
        native_chars=frozenset("абвгдеёжзийклмнопрстуфхцчшщъыьэюя"),
        block_english_pollution=True,
    ),
    "ar": LanguageProfile(
        code="ar",
        label="العربية",
        generic_modifiers=(
            "مجاني", "مشاهدة", "بث", "قائمة", "أفضل",
            "دليل", "منتدى", "جديد", "شائع", "موقع",
        ),
        stopwords=_AR_STOPS,
        native_suffixes=(),
        native_chars=frozenset("ابتثجحخدذرزسشصضطظعغفقكلمنهوي"),
        block_english_pollution=True,
    ),
    "nl": LanguageProfile(
        code="nl",
        label="Nederlands",
        generic_modifiers=(
            "gratis", "kijken", "stream", "online", "lijst",
            "beste", "gids", "forum", "prijs", "nieuw",
        ),
        stopwords=_NL_STOPS,
        native_suffixes=("heid", "ing", "lijk", "baar", "isch"),
        native_chars=frozenset("ëïéè"),
        block_english_pollution=True,
    ),
    "pl": LanguageProfile(
        code="pl",
        label="Polski",
        generic_modifiers=(
            "darmowy", "oglądać", "stream", "online", "lista",
            "najlepszy", "forum", "cena", "nowy", "popularny",
        ),
        stopwords=_PL_STOPS,
        native_suffixes=("acja", "ość", "osc", "enie", "owy", "owa", "owe"),
        native_chars=frozenset("ąćęłńóśźż"),
        block_english_pollution=True,
    ),
    "tr": LanguageProfile(
        code="tr",
        label="Türkçe",
        generic_modifiers=(
            "ücretsiz", "izle", "stream", "online", "liste",
            "en iyi", "rehber", "forum", "fiyat", "yeni",
        ),
        stopwords=_TR_STOPS,
        native_suffixes=("lik", "lık", "luk", "lük", "siz", "sız", "mez", "maz"),
        native_chars=frozenset("çğıöşü"),
        block_english_pollution=True,
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
    profile = get_lang_profile(lang)
    return profile.code


def get_preset(preset_id: str) -> QualityPreset:
    return QUALITY_PRESETS.get(preset_id, QUALITY_PRESETS[DEFAULT_PRESET_ID])
