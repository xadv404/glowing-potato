from dataclasses import dataclass


@dataclass(frozen=True)
class QualityPreset:
    id: str
    label: str
    description: str
    max_per_seed: int
    max_per_prefix: int
    max_per_root: int


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

# Alias compat
SCORE_PRESETS = QUALITY_PRESETS


def get_preset(preset_id: str) -> QualityPreset:
    return QUALITY_PRESETS.get(preset_id, QUALITY_PRESETS[DEFAULT_PRESET_ID])
