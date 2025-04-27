from pydantic import BaseModel
from datetime import datetime, date
from typing import List
import uuid


class Topic(BaseModel):
    id: uuid.UUID
    topic_name: str
    topic_image: str


class TopicCreateModel(BaseModel):
    topic_name: str
    topic_image: str


class TopicUpdateModel(BaseModel):
    topic_name: str
    topic_image: str
