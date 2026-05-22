from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.core.config import config
from src.dress.models import (
    Brightness,
    Category,
    Dress,
    DressCreate,
    DressStatus,
    Formality,
    Layering,
    Pattern,
    Season,
    WarmthLevel,
)


def _normalize_hex(value: str) -> str:
    v = value.strip().lower()
    if not v.startswith("#"):
        v = "#" + v
    if len(v) == 4:
        v = "#" + "".join(c * 2 for c in v[1:])
    if len(v) != 7:
        raise ValueError(f"invalid hex color: {value!r}")
    int(v[1:], 16)
    return v


class DressVisionMultiResult(BaseModel):
    """JSON schema sent to Gemma when cataloging all garments in one image."""

    items: list["DressVisionResult"] = Field(
        min_length=1,
        description=(
            "One entry per distinct garment or wearable visible in the image "
            "(e.g. top, bottom, shoes, socks, hat, accessory in an outfit photo)"
        ),
    )


class DressVisionResult(BaseModel):
    """Vision metadata for a single clothing item."""

    item_name: str = Field(description="Short human-readable name of the garment")
    category: Category = Field(
        description="One of: top, bottom, outerwear, shoes, socks, accessory, "
        "dress, underwear, bag, hat, other"
    )
    colors: list[str] = Field(
        default_factory=list,
        description="All visible colors as #rrggbb hex strings",
    )
    dominant_color: str = Field(description="Primary color as #rrggbb")
    warmth_level: WarmthLevel = Field(
        description="One of: light, medium, heavy"
    )
    season_suitability: list[Season] = Field(
        default_factory=list,
        description="One or more of: summer, winter, spring, fall, all_season",
    )
    style: list[str] = Field(
        default_factory=list,
        description="Short style tags, e.g. casual, formal, streetwear",
    )
    description: str = Field(
        description="Concise visual description (1-3 sentences)"
    )
    layering: Layering = Field(description="One of: base, mid, outer")
    pattern: Optional[Pattern] = Field(
        default=None,
        description="One of: solid, striped, plaid, floral, graphic, other",
    )
    material: Optional[str] = Field(
        default=None, description="Best guess of fabric, e.g. cotton, wool, denim"
    )
    formality: Optional[Formality] = Field(
        default=None,
        description="One of: casual, smart_casual, business, formal",
    )
    brightness: Optional[Brightness] = Field(
        default=None, description="One of: light, dark, mixed"
    )
    water_resistant: bool = Field(default=False)
    occasion_tags: list[str] = Field(
        default_factory=list,
        description="Short occasion tags, e.g. work, party, outdoor, gym",
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Model confidence from 0 to 1"
    )

    @field_validator("colors", mode="before")
    @classmethod
    def _v_colors(cls, v):
        if not isinstance(v, list):
            return v
        return [_normalize_hex(c) for c in v]

    @field_validator("dominant_color", mode="before")
    @classmethod
    def _v_dominant(cls, v):
        return _normalize_hex(v) if isinstance(v, str) else v

    def to_dress_create(self) -> DressCreate:
        return DressCreate(
            item_name=self.item_name,
            category=self.category,
            colors=list(self.colors),
            dominant_color=self.dominant_color,
            warmth_level=self.warmth_level,
            season_suitability=list(self.season_suitability),
            style=list(self.style),
            description=self.description,
            layering=self.layering,
            pattern=self.pattern,
            material=self.material,
            formality=self.formality,
            brightness=self.brightness,
            water_resistant=self.water_resistant,
            occasion_tags=list(self.occasion_tags),
        )

    def apply_ai_metadata(self, dress: Dress) -> None:
        dress.ai_model_version = config.gemma_model_id
        dress.ai_processed_at = datetime.now(timezone.utc)
        dress.ai_confidence = self.confidence
        confidence = self.confidence
        if confidence is None or confidence >= 0.5:
            dress.status = DressStatus.ready
        else:
            dress.status = DressStatus.needs_review


class DressCatalogItem(BaseModel):
    """Slim wardrobe item shape sent to Gemma for outfit selection."""

    id: int
    item_name: Optional[str] = None
    category: Optional[Category] = None
    colors: list[str] = Field(default_factory=list)
    dominant_color: Optional[str] = None
    warmth_level: Optional[WarmthLevel] = None
    season_suitability: list[Season] = Field(default_factory=list)
    style: list[str] = Field(default_factory=list)
    formality: Optional[Formality] = None
    brightness: Optional[Brightness] = None
    layering: Optional[Layering] = None
    pattern: Optional[Pattern] = None
    material: Optional[str] = None
    water_resistant: bool = False
    occasion_tags: list[str] = Field(default_factory=list)
    description: Optional[str] = None

    @classmethod
    def from_dress(cls, dress: Dress) -> "DressCatalogItem":
        return cls(
            id=dress.id,
            item_name=dress.item_name,
            category=dress.category,
            colors=list(dress.colors or []),
            dominant_color=dress.dominant_color,
            warmth_level=dress.warmth_level,
            season_suitability=list(dress.season_suitability or []),
            style=list(dress.style or []),
            formality=dress.formality,
            brightness=dress.brightness,
            layering=dress.layering,
            pattern=dress.pattern,
            material=dress.material,
            water_resistant=dress.water_resistant,
            occasion_tags=list(dress.occasion_tags or []),
            description=dress.description,
        )


class OutfitPiece(BaseModel):
    dress_id: int = Field(description="ID from the provided wardrobe catalog")
    category: Category = Field(description="Category of the wardrobe piece")
    role: str = Field(
        description=(
            "Role in the outfit, e.g. 'top', 'bottom', 'outerwear', "
            "'shoes', 'accessory'"
        )
    )


class OutfitSuggestion(BaseModel):
    name: str = Field(description="Short label for the outfit")
    pieces: list[OutfitPiece] = Field(
        description=(
            "Selected wardrobe pieces. Include at minimum a top, a bottom, "
            "and shoes when available. Add outerwear/accessories when the "
            "weather or event warrants it."
        )
    )
    color_harmony: str = Field(
        description=(
            "Brief explanation of how the colors of the pieces work together "
            "(complementary, analogous, neutral anchor, etc.)"
        )
    )
    reasoning: str = Field(
        description=(
            "Why this outfit suits the event, weather, season, and time of day."
        )
    )


class OutfitSuggestionsResult(BaseModel):
    outfits: list[OutfitSuggestion] = Field(
        description="Provide at least 2 distinct complete outfits."
    )
    weather_summary: Optional[str] = Field(
        default=None,
        description=(
            "Concise summary of the relevant weather conditions for the event."
        ),
    )


DressVisionMultiResult.model_rebuild()
