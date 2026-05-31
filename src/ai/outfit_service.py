import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.prompts import OUTFIT_SUGGESTION_PROMPT
from src.ai.schemas import (
    DressCatalogItem,
    OutfitSuggestionsResult,
)
from src.ai.tool_runner import run_with_tools
from src.ai.tools import AVAILABLE_TOOLS, TOOL_DECLARATIONS
from src.auth.models import User
from src.dress.models import DressRead
from src.dress.service import DressService
from src.event.models import Event
from src.event.season import season_for_date
from src.event.service import EventService

logger = logging.getLogger(__name__)

MIN_OUTFITS = 2


class OutfitSuggestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def suggest_for_event(
        self,
        user: User,
        event: Event,
        event_service: EventService,
        dress_service: DressService,
    ) -> dict[str, Any]:
        season = season_for_date(event.event_date)

        dresses = await dress_service.list_for_outfit_suggestion(user, season)
        if len(dresses) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Not enough wardrobe items match this season to build "
                    "outfits. Upload more clothes or analyze the existing ones."
                ),
            )

        catalog = [DressCatalogItem.from_dress(d) for d in dresses]
        dresses_by_id = {d.id: d for d in dresses}

        event_payload = {
            "event_type": event.event_type,
            "event_date": event.event_date.isoformat(),
            "start_time": event.start_time.isoformat() if event.start_time else None,
            "end_time": event.end_time.isoformat() if event.end_time else None,
            "city": event.city_obj.display_name if event.city_obj else event.city,
            "season": season.value,
            "title": event.title,
            "notes": event.notes,
        }

        user_prompt = (
            f"{OUTFIT_SUGGESTION_PROMPT}\n\n"
            f"Event:\n{json.dumps(event_payload, indent=2)}\n\n"
            f"Wardrobe catalog ({len(catalog)} items):\n"
            f"{json.dumps([c.model_dump(mode='json') for c in catalog], indent=2)}"
        )

        try:
            text, _ = await run_with_tools(
                contents=[user_prompt],
                tools=TOOL_DECLARATIONS,
                available_tools=AVAILABLE_TOOLS,
                final_response_schema=OutfitSuggestionsResult,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Outfit suggestion AI call failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI outfit suggestion failed: {exc}",
            ) from exc

        if not text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="AI returned an empty outfit suggestion response",
            )

        try:
            result = OutfitSuggestionsResult.model_validate_json(text)
        except ValueError as exc:
            logger.error("Outfit result invalid JSON: %s", text[:500])
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"AI returned invalid outfit JSON: {exc}",
            ) from exc

        valid_outfits = []
        for outfit in result.outfits:
            valid_pieces = [
                piece for piece in outfit.pieces if piece.dress_id in dresses_by_id
            ]
            if not valid_pieces:
                continue
            outfit_copy = outfit.model_copy(update={"pieces": valid_pieces})
            valid_outfits.append(outfit_copy)

        if len(valid_outfits) < MIN_OUTFITS:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    f"AI returned only {len(valid_outfits)} valid outfit(s); "
                    f"expected at least {MIN_OUTFITS}."
                ),
            )

        outfits_payload = []
        for outfit in valid_outfits:
            outfits_payload.append(
                {
                    "name": outfit.name,
                    "color_harmony": outfit.color_harmony,
                    "reasoning": outfit.reasoning,
                    "pieces": [
                        {
                            "dress_id": piece.dress_id,
                            "category": piece.category,
                            "role": piece.role,
                            "dress": DressRead.model_validate(
                                dresses_by_id[piece.dress_id],
                                from_attributes=True,
                            ).model_dump(mode="json"),
                        }
                        for piece in outfit.pieces
                    ],
                }
            )

        payload = {
            "event_id": event.id,
            "season": season.value,
            "weather_summary": result.weather_summary,
            "outfits": outfits_payload,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        await event_service.save_outfit_suggestions(event, payload)
        return payload
