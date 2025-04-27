from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional
from src.ai.schemas import AiTranslationServiceResultModel
from src.speeches.schemas import SpeechCreateModel, SpeechUpdateModel
from src.people.schemas import PersonCreateModel, PersonUpdateModel
from src.topic.schemas import TopicCreateModel, TopicUpdateModel
import uuid


class Translation(BaseModel):
    id: uuid.UUID
    speech_id: uuid.UUID
    original: str
    translation: str


class TranslationCreateModel(BaseModel):
    speech_id: uuid.UUID
    original: str
    translation: str


class TranslationUpdateModel(BaseModel):
    speech_id: uuid.UUID
    original: str
    translation: str


class SpeakerInfo(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    info: str
    person_image: Optional[str] = None
    create: bool
    org: str
    long_summary: Optional[str] = None
    short_summary: Optional[str] = None


class TopicInfo(BaseModel):
    id: Optional[uuid.UUID] = None
    name: str
    create: bool
    topic_image: Optional[str] = None


class TranslationCreateRequest(BaseModel):
    speech_id: Optional[uuid.UUID] = None
    speakers: List[SpeakerInfo]
    url: str
    context: Optional[str] = None
    topics: List[TopicInfo]
    createSpeech: bool
    cover_url: Optional[str]
    transcript: str


class YoutubeInfo(BaseModel):
    title: str
    uploader: str
    publish_date: str
    language: str
    transcript: Optional[str] = None
    duration: str
    duration_in_seconds: int


class BrandNewTranslationUpdateModel(BaseModel):
    ai_translation_response: AiTranslationServiceResultModel
    create_speeches: List[SpeechCreateModel]
    update_speeches: List[SpeechUpdateModel]
    create_people: List[PersonCreateModel]
    update_people: List[PersonUpdateModel]
    create_topic: List[TopicCreateModel]
    update_topic: List[TopicUpdateModel]
