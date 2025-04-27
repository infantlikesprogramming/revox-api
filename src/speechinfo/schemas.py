from pydantic import BaseModel
from datetime import datetime, date


class UrlServiceRequest(BaseModel):
    url: str


class YoutubeInfoResponse(BaseModel):
    title: str
    uploader: str
    publish_date: str
    language: str
    duration: str
