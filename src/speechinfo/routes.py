from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from .schemas import UrlServiceRequest
from pydantic import BaseModel
from src.utils import get_video_info_from_url, YoutubeInfoResponse


speechinfo_router = APIRouter()


@speechinfo_router.post(
    "/", status_code=status.HTTP_200_OK, response_model=YoutubeInfoResponse
)
async def create_url_information(url: UrlServiceRequest) -> dict:
    result: YoutubeInfoResponse = await get_video_info_from_url(url.url)

    return result
