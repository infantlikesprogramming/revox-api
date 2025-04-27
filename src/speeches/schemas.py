from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
import uuid


class Speech(BaseModel):
    id: uuid.UUID
    title: str
    topic_name: str
    topic_ids: List[uuid.UUID]
    people_ids: List[uuid.UUID]
    source_image: str
    source_url: str
    publish_date: datetime
    source_owner: str
    language: str
    duration: str
    audio_url: str
    speech_summary: str
    cover_url: str
    translation_id: List[uuid.UUID]


class SpeechCreateModel(BaseModel):
    title: str
    topic_name: str
    topic_ids: List[uuid.UUID]
    people_ids: List[uuid.UUID]
    source_image: str
    source_url: str
    publish_date: str
    source_owner: str
    language: str
    duration: str
    audio_url: str
    speech_summary: str
    cover_url: str
    translation_id: List[uuid.UUID]


class SpeechUpdateModel(BaseModel):
    title: str
    topic_name: str
    topic_ids: List[uuid.UUID]
    people_ids: List[uuid.UUID]
    source_image: str
    publish_date: datetime
    source_owner: str
    language: str
    duration: str
    audio_url: str
    speech_summary: str
    cover_url: str
    translation_id: Optional[List[uuid.UUID]] = None
