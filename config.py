from dataclasses import dataclass


@dataclass(frozen=True)
class ScorePreset:
    id: str
    label: str
    description: str
    min_score: int
    max_per_seed: int
    max_per_prefix: int
    max_per_root: int


SCORE_PRESETS: dict[str, ScorePreset] = {
    "strict": ScorePreset(
        id="strict",
        label="Strict (HQ)",
        description=(
            "Score minimum 6 — keyword confirmé sur 3 sources (Google + YouTube + Bing). "
            "Peu de résultats, qualité maximale."
        ),
        min_score=6,
        max_per_seed=15,
        max_per_prefix=2,
        max_per_root=1,
    ),
    "balanced": ScorePreset(
        id="balanced",
        label="Équilibré (recommandé)",
        description=(
            "Score minimum 4 — 2 sources ou suggestion directe + 1 source. "
            "Bon compromis qualité / volume."
        ),
        min_score=4,
        max_per_seed=25,
        max_per_prefix=3,
        max_per_root=2,
    ),
    "permissive": ScorePreset(
        id="permissive",
        label="Permissif",
        description=(
            "Score minimum 2 — 1 source suffit. Plus de keywords, "
            "filtrage thème toujours actif."
        ),
        min_score=2,
        max_per_seed=35,
        max_per_prefix=4,
        max_per_root=2,
    ),
    "volume": ScorePreset(
        id="volume",
        label="Volume max",
        description=(
            "Score minimum 2, limites assouplies. Maximum de keywords "
            "pour grosses listes de seeds."
        ),
        min_score=2,
        max_per_seed=45,
        max_per_prefix=5,
        max_per_root=3,
    ),
}

DEFAULT_PRESET_ID = "balanced"


def get_preset(preset_id: str) -> ScorePreset:
    return SCORE_PRESETS.get(preset_id, SCORE_PRESETS[DEFAULT_PRESET_ID])


def preset_choices() -> list[tuple[str, str]]:
    return [(p.id, p.label) for p in SCORE_PRESETS.values()]
