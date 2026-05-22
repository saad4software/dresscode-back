from typing import Annotated

from fastapi import Depends

from src.ai.outfit_service import OutfitSuggestionService
from src.ai.service import AIService
from src.core.dependencies import SessionDep


def get_ai_service(session: SessionDep) -> AIService:
    return AIService(session)


def get_outfit_service(session: SessionDep) -> OutfitSuggestionService:
    return OutfitSuggestionService(session)


AIServiceDep = Annotated[AIService, Depends(get_ai_service)]
OutfitServiceDep = Annotated[
    OutfitSuggestionService, Depends(get_outfit_service)
]
