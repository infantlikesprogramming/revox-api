from pydantic import BaseModel
from datetime import datetime, date
from typing import List
import uuid


class Person(BaseModel):
    id: uuid.UUID
    person_name: str
    organization: str
    person_image: str
    short_summary: str
    long_summary: str
    speeches_id: List[uuid.UUID]


class PersonCreateModel(BaseModel):
    person_name: str
    organization: str
    person_image: str
    short_summary: str
    long_summary: str
    speeches_id: List[uuid.UUID]


class PersonUpdateModel(BaseModel):
    person_name: str
    organization: str
    person_image: str
    short_summary: str
    long_summary: str
    speeches_id: List[uuid.UUID]
