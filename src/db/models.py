from sqlmodel import SQLModel, Field, Column, Relationship
import sqlalchemy.dialects.postgresql as pg
from datetime import datetime, date
import uuid
from typing import List, Optional


class Speeches(SQLModel, table=True):
    __tablename__ = "speeches"
    id: uuid.UUID = Field(
        sa_column=Column(pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4)
    )
    title: str = Field(sa_column=(Column(pg.VARCHAR(511), nullable=False)))
    topic_name: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    topic_ids: List[uuid.UUID] = Field(
        sa_column=Column(pg.ARRAY(pg.UUID), nullable=False, default=[])
    )
    people_ids: List[uuid.UUID] = Field(
        sa_column=Column(pg.ARRAY(pg.UUID), nullable=False, default=[])
    )
    source_image: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))

    source_url: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))
    publish_date: datetime = (Field(sa_column=Column(pg.TIMESTAMP)),)
    source_owner: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    language: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    duration: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    audio_url: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    speech_summary: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))
    cover_url: str = (Field(sa_column=(Column(pg.TEXT, nullable=False))),)
    translation_id: List[uuid.UUID] = Field(
        sa_column=Column(pg.ARRAY(pg.UUID), nullable=False, default=[])
    )


class People(SQLModel, table=True):
    __tablename__ = "people"
    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4, unique=True
        )
    )
    person_name: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    organization: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    person_image: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))
    short_summary: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))
    long_summary: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))
    speeches_id: List[uuid.UUID] = Field(
        sa_column=Column(pg.ARRAY(pg.UUID), nullable=False, default=[])
    )


class Topics(SQLModel, table=True):
    __tablename__ = "topics"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4, unique=True
        )
    )
    topic_name: str = Field(sa_column=(Column(pg.VARCHAR(255), nullable=False)))
    topic_image: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))


class Translations(SQLModel, table=True):
    __tablename__ = "translations"

    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID, nullable=False, primary_key=True, default=uuid.uuid4, unique=True
        )
    )
    speech_id: uuid.UUID = Field(foreign_key="speeches.id", nullable=False)
    original: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))
    translation: str = Field(sa_column=(Column(pg.TEXT, nullable=False)))
