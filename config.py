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
    modifiers: tuple[str, ...]
    acceptable_words: frozenset[str]
    native_suffixes: tuple[str, ...]
    native_chars: frozenset[str]
    block_english_pollution: bool


# Presets de filtrage / dédup (autocomplete Google + filtre thème intelligent).
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


class UnsupportedLanguageError(ValueError):
    """Langue hl non maîtrisée — pas de fallback."""

    def __init__(self, lang: str) -> None:
        self.lang = lang
        codes = ", ".join(profile.code for profile in LANGUAGE_PROFILES.values())
        super().__init__(
            f"Langue « {lang} » non maîtrisée.\n"
            f"Nous ne disposons pas de filtrage ni de modificateurs pour cette langue.\n"
            f"Langues supportées : {codes}"
        )

# Alias compat
SCORE_PRESETS = QUALITY_PRESETS

# Langues sans casse (ne pas lower() les keywords).
CASELESS_LANGS = frozenset({"ja", "ko", "zh", "zh-cn", "zh-tw", "zh-hk"})

# Mots acceptés par langue (en plus des ancres thème universelles).
_FR_WORDS = frozenset({
    "action", "combat", "aventure", "aventureux", "romance", "romantique", "horreur",
    "comédie", "comedie", "drame", "dramatique", "fantasy", "magie", "surnaturel",
    "cyberpunk", "ecchi", "harem", "isekai", "shonen", "seinen", "mecha", "vostfr",
    "manga", "anime", "figurine", "cosplay", "opening", "scan", "scantrad", "fansub",
    "crunchyroll", "wakanim", "netflix", "otaku", "kawaii", "chibi", "yaoi", "yuri",
    "japonais", "japonesa", "chinois", "francais", "français", "gratuit", "complet",
    "streaming", "legal", "légal", "populaire", "culte", "nouveau", "nouveauté",
    "liste", "saison", "episode", "épisode", "film", "films", "serie", "série",
    "regarder", "voir", "site", "forum", "avis", "prix", "guide", "top", "meilleur",
    "scolaire", "edgerunners", "kyoani", "ufotable", "mappa", "ghibli", "toei",
    "bones", "trigger", "madhouse", "costume", "collector", "peluche", "poster",
    "goodies", "artbook", "coffret", "sticker", "doujin", "webtoon", "simulcast",
    "tankobon", "mangaka", "seiyu", "abonnement", "catalogue", "plateforme",
})

_EN_WORDS = frozenset({
    "adventure", "comedy", "romance", "horror", "drama", "fantasy", "magic", "supernatural",
    "cyberpunk", "ecchi", "harem", "isekai", "shonen", "seinen", "mecha", "sub", "dub",
    "manga", "anime", "figure", "figures", "cosplay", "opening", "scan", "fansub",
    "crunchyroll", "funimation", "wakanim", "netflix", "otaku", "kawaii", "chibi",
    "yaoi", "yuri", "watch", "stream", "streaming", "online", "free", "legal", "complete",
    "popular", "new", "list", "best", "top", "review", "guide", "site", "forum", "price",
    "season", "episode", "episodes", "movie", "movies", "series", "download", "english",
    "japanese", "chinese", "korean", "simulcast", "webtoon", "light", "novel", "mangaka",
    "seiyu", "poster", "goodies", "artbook", "peluche", "sticker", "coffret", "doujin",
    "catalog", "platform", "subscription", "upcoming", "recent", "classic", "cult",
    "action", "thriller", "survival", "historical", "psychological", "school", "life",
})

_ES_WORDS = frozenset({
    "anime", "manga", "gratis", "ver", "streaming", "completo", "episodio", "temporada",
    "lista", "mejor", "top", "guia", "guía", "foro", "precio", "legal", "nuevo", "popular",
    "netflix", "crunchyroll", "cosplay", "figurine", "figura", "opening", "scan", "vostfr",
    "subtitulado", "doblado", "aventura", "romance", "horror", "comedia", "drama", "fantasia",
    "fantasía", "accion", "acción", "isekai", "shonen", "seinen", "mecha", "otaku", "kawaii",
    "pelicula", "película", "serie", "series", "temporada", "capitulo", "capítulo",
    "descargar", "online", "gratuito", "novedad", "clasico", "clásico", "culto", "fansub",
})

_DE_WORDS = frozenset({
    "anime", "manga", "gratis", "kostenlos", "stream", "streaming", "online", "komplett",
    "folge", "staffel", "liste", "beste", "top", "guide", "forum", "preis", "legal", "neu",
    "popular", "beliebt", "netflix", "crunchyroll", "cosplay", "figur", "figure", "opening",
    "scan", "vostfr", "untertitel", " synchron", "abenteuer", "romantik", "horror", "komödie",
    "komodie", "drama", "fantasy", "aktion", "isekai", "shonen", "seinen", "mecha", "otaku",
    "kawaii", "film", "filme", "serie", "serien", "staffel", "episode", "episoden",
    "kostenfrei", "gratis", "neuheit", "klassiker", "kult", "fansub", "sehen", "schauen",
})

_PT_WORDS = frozenset({
    "anime", "manga", "gratis", "grátis", "ver", "streaming", "completo", "episodio", "episódio",
    "temporada", "lista", "melhor", "top", "guia", "forum", "fórum", "preco", "preço", "legal",
    "novo", "popular", "netflix", "crunchyroll", "cosplay", "figurine", "figura", "opening",
    "scan", "vostfr", "legendado", "dublado", "aventura", "romance", "horror", "comedia",
    "comédia", "drama", "fantasia", "acao", "ação", "isekai", "shonen", "seinen", "mecha",
    "otaku", "kawaii", "filme", "filmes", "serie", "série", "series", "séries", "temporada",
    "capitulo", "capítulo", "online", "gratuito", "classico", "clássico", "culto", "fansub",
})

_IT_WORDS = frozenset({
    "anime", "manga", "gratis", "gratuito", "vedere", "streaming", "completo", "episodio",
    "stagione", "lista", "migliore", "top", "guida", "forum", "prezzo", "legale", "nuovo",
    "popolare", "netflix", "crunchyroll", "cosplay", "figurine", "opening", "scan", "vostfr",
    "sottotitolato", "doppiato", "avventura", "romance", "horror", "commedia", "dramma",
    "fantasia", "azione", "isekai", "shonen", "seinen", "mecha", "otaku", "kawaii", "film",
    "serie", "online", "classico", "culto", "fansub",
})

_RU_WORDS = frozenset({
    "аниме", "манга", "смотреть", "стрим", "стриминг", "онлайн", "бесплатно", "полный",
    "серия", "сезон", "список", "лучший", "топ", "гид", "форум", "цена", "легально",
    "новый", "популярный", "netflix", "косплей", "фигурка", "опенинг", "скан", "субтитры",
    "приключения", "романтика", "ужасы", "комедия", "драма", "фэнтези", "экшен", "isekai",
    "shonen", "seinen", "mecha", "otaku", "kawaii", "фильм", "сериал", "эпизод", "классика",
})

_AR_WORDS = frozenset({
    "anime", "manga", "مجاني", "مشاهدة", "بث", "مباشر", "كامل", "حلقة", "موسم", "قائمة",
    "افضل", "أفضل", "دليل", "منتدى", "سعر", "قانوني", "جديد", "شائع", "netflix", "cosplay",
    "مغامرة", "رومانس", "رعب", "كوميديا", "دراما", "isekai", "shonen", "seinen",
})

_JA_WORDS = frozenset({
    "アニメ", "マンガ", "漫画", "無料", "配信", "視聴", "ストリーミング", "一覧", "おすすめ",
    "新作", "人気", "話", "巻", "期", "シーズン", "エピソード", "映画", "anime", "manga",
    "cosplay", "コスプレ", "フィギュア", "figurine", "opening", "オープニング", "scan",
    "scantrad", "vostfr", "isekai", "shonen", "seinen", "mecha", "otaku", "kawaii", "netflix",
    "crunchyroll", "fansub", "webtoon", "doujin", "同人", "声優", "seiyu", "mangaka", "漫画家",
})

_KO_WORDS = frozenset({
    "애니", "애니메", "만화", "무료", "스트리밍", "시청", "온라인", "완결", "에피소드", "시즌",
    "목록", "추천", "인기", "신작", "anime", "manga", "cosplay", "코스프레", "피규어", "opening",
    "scan", "vostfr", "isekai", "shonen", "seinen", "mecha", "otaku", "kawaii", "netflix",
    "crunchyroll", "fansub", "webtoon", "doujin", "성우", "seiyu", "mangaka",
})

_ZH_WORDS = frozenset({
    "动漫", "动画", "漫画", "免费", "在线", "观看", "流媒体", "完整", "集", "季", "列表",
    "推荐", "热门", "新作", "anime", "manga", "cosplay", "手办", "opening", "scan", "vostfr",
    "isekai", "shonen", "seinen", "mecha", "otaku", "kawaii", "netflix", "crunchyroll",
    "fansub", "webtoon", "doujin", "声优", "seiyu", "mangaka", "番剧", "新番", "完结",
})

LANGUAGE_PROFILES: dict[str, LanguageProfile] = {
    "fr": LanguageProfile(
        code="fr",
        label="Français",
        modifiers=(
            "gratuit", "vostfr", "vf", "streaming", "legal", "complet", "voir", "regarder",
            "site", "liste", "top", "meilleur", "forum", "avis", "prix", "guide",
            "saison", "episode", "film", "nouveau", "populaire", "culte",
            "netflix", "crunchyroll", "adn", "wakanim", "figurine", "cosplay",
            "opening", "scan", "france", "francais", "telecharger", "sans", "pub",
        ),
        acceptable_words=_FR_WORDS,
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
        modifiers=(
            "free", "watch", "stream", "online", "full", "episode", "season", "list", "best",
            "top", "review", "guide", "site", "forum", "price", "download", "legal", "complete",
            "popular", "new", "netflix", "crunchyroll", "funimation", "cosplay", "figure",
            "opening", "scan", "sub", "dub", "english", "where", "how",
        ),
        acceptable_words=_EN_WORDS,
        native_suffixes=("tion", "ness", "ment", "ing", "ous", "ful", "ive", "able", "ish"),
        native_chars=frozenset(),
        block_english_pollution=False,
    ),
    "es": LanguageProfile(
        code="es",
        label="Español",
        modifiers=(
            "gratis", "ver", "streaming", "completo", "episodio", "temporada", "lista", "mejor",
            "top", "guia", "foro", "precio", "legal", "nuevo", "popular", "netflix", "crunchyroll",
            "cosplay", "figurine", "opening", "scan", "online", "descargar", "subtitulado",
        ),
        acceptable_words=_ES_WORDS,
        native_suffixes=("ción", "cion", "dad", "mente", "ado", "ada", "oso", "osa", "aje"),
        native_chars=frozenset("áéíóúüñ"),
        block_english_pollution=True,
    ),
    "de": LanguageProfile(
        code="de",
        label="Deutsch",
        modifiers=(
            "gratis", "kostenlos", "stream", "online", "komplett", "folge", "staffel", "liste",
            "beste", "top", "guide", "forum", "preis", "legal", "neu", "popular", "netflix",
            "crunchyroll", "cosplay", "figur", "opening", "scan", "sehen", "schauen",
        ),
        acceptable_words=_DE_WORDS,
        native_suffixes=("ung", "heit", "keit", "lich", "isch", "los", "bar", "ieren"),
        native_chars=frozenset("äöüß"),
        block_english_pollution=True,
    ),
    "pt": LanguageProfile(
        code="pt",
        label="Português",
        modifiers=(
            "gratis", "grátis", "ver", "streaming", "completo", "episodio", "temporada", "lista",
            "melhor", "top", "guia", "forum", "preco", "legal", "novo", "popular", "netflix",
            "crunchyroll", "cosplay", "figurine", "opening", "scan", "online", "legendado",
        ),
        acceptable_words=_PT_WORDS,
        native_suffixes=("ção", "cao", "dade", "mente", "ado", "ada", "oso", "osa", "agem"),
        native_chars=frozenset("áâãàéêíóôõúç"),
        block_english_pollution=True,
    ),
    "it": LanguageProfile(
        code="it",
        label="Italiano",
        modifiers=(
            "gratis", "gratuito", "vedere", "streaming", "completo", "episodio", "stagione",
            "lista", "migliore", "top", "guida", "forum", "prezzo", "legale", "nuovo", "popolare",
            "netflix", "crunchyroll", "cosplay", "figurine", "opening", "scan", "online",
        ),
        acceptable_words=_IT_WORDS,
        native_suffixes=("zione", "mente", "ato", "ata", "oso", "osa", "aggio", "ità", "ita"),
        native_chars=frozenset("àèéìíîòóù"),
        block_english_pollution=True,
    ),
    "ja": LanguageProfile(
        code="ja",
        label="日本語",
        modifiers=(
            "アニメ", "マンガ", "無料", "配信", "視聴", "一覧", "おすすめ", "新作", "人気",
            "ネットflix", "ストリーミング", "コスプレ", "フィギュア", "オープニング", "scan",
            "vostfr", "完全", "最新", "ランキング",
        ),
        acceptable_words=_JA_WORDS,
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=True,
    ),
    "ko": LanguageProfile(
        code="ko",
        label="한국어",
        modifiers=(
            "애니", "애니메", "만화", "무료", "스트리밍", "시청", "온라인", "완결", "추천", "인기",
            "신작", "목록", "코스프레", "피규어", "opening", "scan", "vostfr", "최신", "랭킹",
        ),
        acceptable_words=_KO_WORDS,
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=True,
    ),
    "zh-cn": LanguageProfile(
        code="zh-CN",
        label="中文 (简体)",
        modifiers=(
            "动漫", "动画", "漫画", "免费", "在线", "观看", "完整", "推荐", "热门", "新作",
            "列表", "cosplay", "手办", "opening", "scan", "vostfr", "最新", "排行", "番剧",
        ),
        acceptable_words=_ZH_WORDS,
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=True,
    ),
    "zh-tw": LanguageProfile(
        code="zh-TW",
        label="中文 (繁體)",
        modifiers=(
            "動漫", "動畫", "漫畫", "免費", "線上", "觀看", "完整", "推薦", "熱門", "新作",
            "列表", "cosplay", "公仔", "opening", "scan", "vostfr", "最新", "排行", "番劇",
        ),
        acceptable_words=_ZH_WORDS | frozenset({
            "動漫", "動畫", "漫畫", "免費", "線上", "觀看", "推薦", "熱門", "新作", "番劇",
        }),
        native_suffixes=(),
        native_chars=frozenset(),
        block_english_pollution=True,
    ),
    "ru": LanguageProfile(
        code="ru",
        label="Русский",
        modifiers=(
            "аниме", "манга", "смотреть", "онлайн", "бесплатно", "полный", "серия", "сезон",
            "список", "лучший", "топ", "форум", "цена", "новый", "популярный", "cosplay",
            "фигурка", "opening", "scan", "vostfr", "стриминг",
        ),
        acceptable_words=_RU_WORDS,
        native_suffixes=("ция", "ость", "ение", "ный", "ная", "ное", "ский", "ская"),
        native_chars=frozenset("абвгдеёжзийклмнопрстуфхцчшщъыьэюя"),
        block_english_pollution=True,
    ),
    "ar": LanguageProfile(
        code="ar",
        label="العربية",
        modifiers=(
            "anime", "manga", "مجاني", "مشاهدة", "بث", "مباشر", "كامل", "حلقة", "موسم", "قائمة",
            "افضل", "دليل", "منتدى", "جديد", "شائع", "cosplay", "opening", "scan",
        ),
        acceptable_words=_AR_WORDS,
        native_suffixes=(),
        native_chars=frozenset("ابتثجحخدذرزسشصضطظعغفقكلمنهوي"),
        block_english_pollution=True,
    ),
    "nl": LanguageProfile(
        code="nl",
        label="Nederlands",
        modifiers=(
            "gratis", "kijken", "stream", "online", "compleet", "aflevering", "seizoen", "lijst",
            "beste", "top", "gids", "forum", "prijs", "nieuw", "populair", "netflix", "crunchyroll",
            "cosplay", "figuur", "opening", "scan",
        ),
        acceptable_words=_EN_WORDS | frozenset({
            "gratis", "kijken", "stream", "online", "compleet", "aflevering", "seizoen", "lijst",
            "beste", "gids", "forum", "prijs", "nieuw", "populair", "figuur", "anime", "manga",
        }),
        native_suffixes=("heid", "ing", "lijk", "baar", "isch"),
        native_chars=frozenset("ëïéè"),
        block_english_pollution=True,
    ),
    "pl": LanguageProfile(
        code="pl",
        label="Polski",
        modifiers=(
            "darmowy", "ogladac", "oglądać", "stream", "online", "pelny", "pełny", "odcinek",
            "sezon", "lista", "najlepszy", "top", "przewodnik", "forum", "cena", "nowy",
            "popularny", "netflix", "crunchyroll", "cosplay", "figurka", "opening", "scan",
        ),
        acceptable_words=_EN_WORDS | frozenset({
            "anime", "manga", "darmowy", "stream", "online", "odcinek", "sezon", "lista",
            "najlepszy", "forum", "cena", "nowy", "popularny", "figurka", "ogladac", "oglądać",
        }),
        native_suffixes=("acja", "ość", "osc", "enie", "owy", "owa", "owe"),
        native_chars=frozenset("ąćęłńóśźż"),
        block_english_pollution=True,
    ),
    "tr": LanguageProfile(
        code="tr",
        label="Türkçe",
        modifiers=(
            "ucretsiz", "ücretsiz", "izle", "stream", "online", "tam", "bolum", "bölüm", "sezon",
            "liste", "en", "iyi", "top", "rehber", "forum", "fiyat", "yeni", "populer", "popüler",
            "netflix", "crunchyroll", "cosplay", "figur", "opening", "scan",
        ),
        acceptable_words=_EN_WORDS | frozenset({
            "anime", "manga", "ucretsiz", "ücretsiz", "izle", "online", "bolum", "bölüm",
            "sezon", "liste", "rehber", "forum", "fiyat", "yeni", "populer", "popüler", "figur",
        }),
        native_suffixes=("lik", "lık", "luk", "lük", "siz", "sız", "mez", "maz"),
        native_chars=frozenset("çğıöşü"),
        block_english_pollution=True,
    ),
}

# Ordre d'affichage GUI
LANGUAGE_OPTIONS: list[tuple[str, str]] = [
    (profile.code, profile.label) for profile in LANGUAGE_PROFILES.values()
]


def normalize_lang(code: str) -> str:
    """Normalise un code langue Google (hl) vers la clé interne."""
    normalized = code.strip().lower().replace("_", "-")
    if normalized in LANGUAGE_PROFILES:
        return normalized
    # zh-CN / zh-TW
    if normalized.startswith("zh"):
        if "tw" in normalized or "hk" in normalized or "hant" in normalized:
            return "zh-tw"
        return "zh-cn"
    # pt-BR / pt-PT → pt
    if normalized.startswith("pt"):
        return "pt"
    # Fallback : langue principale (en-US → en)
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
    """Code hl exact pour l'API Google."""
    profile = get_lang_profile(lang)
    return profile.code


def get_preset(preset_id: str) -> QualityPreset:
    return QUALITY_PRESETS.get(preset_id, QUALITY_PRESETS[DEFAULT_PRESET_ID])
