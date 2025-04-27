from fastapi import APIRouter, status, Depends
from fastapi.exceptions import HTTPException
from .schemas import (
    AiSpeakerServiceResponseModel,
    AiSpeakerServiceSpeakersRequest,
    AiSpeakerServiceSpeakersDetails,
    AiSpeakerServiceSpeakerInformation,
)
from typing import List
from .service import AiService

ai_router = APIRouter()
ai_service = AiService()


@ai_router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=List[AiSpeakerServiceSpeakerInformation],
)
async def generate_speaker_summaries(
    speakers_data: AiSpeakerServiceSpeakersRequest,
) -> dict:
    speakers = speakers_data.speakers
    speaker_details = AiSpeakerServiceSpeakersDetails(
        speakers=speakers, number_of_speakers=len(speakers)
    )

    return (await ai_service.speaker_service(speaker_details)).speaker_summaries
