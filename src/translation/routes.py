from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi.exceptions import HTTPException
from src.translation.schemas import TranslationCreateRequest
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession

from .service import TranslationService
from src.utils import get_speech_info_from_url, YoutubeInfo

translation_router = APIRouter()
translation_service = TranslationService()


@translation_router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_a_translation(
    translation_data: TranslationCreateRequest,
    bg_task: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict:
    speech_info: YoutubeInfo = await get_speech_info_from_url(translation_data.url)
    if speech_info.duration_in_seconds > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The video is too long."},
        )
    if len(translation_data.transcript.split(" ")) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The transcript is too long."},
        )
    bg_task.add_task(
        translation_service.create_translation_with_ai_and_update_database,
        translation_data,
        session,
    )

    return {"message": "Thank you. Your request has been received"}
