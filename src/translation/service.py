from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import (
    TranslationCreateModel,
    TranslationUpdateModel,
    TranslationCreateRequest,
    YoutubeInfo,
)

from src.ai.schemas import (
    AiTranslationServiceResultModel,
    AiTranslationCreateModel,
    Speaker,
)
from typing import List

from sqlmodel import select, update
from src.db.models import Translations, Speeches
from .utils import speakers_for_ai_service
from src.utils import (
    get_speech_info_from_url,
)
from .utils import (
    update_database_and_create_translation,
    create_tts_audio_and_upload_to_s3,
    update_speech_with_audio_and_translation,
    update_english_summaries,
)
from dotenv import load_dotenv
import os
from src.ai.service import AiService
from src.topic.service import TopicService
from src.people.service import PersonService
from src.speeches.service import SpeechService

topic_service = TopicService()
person_service = PersonService()
speech_service = SpeechService()
ai_service = AiService()

load_dotenv()
cloudfront_url = os.environ.get("CLOUDFRONT_URL")


class TranslationService:
    async def get_translation(self, translation_id, session: AsyncSession):
        statement = select(Translations).where(Translations.id == translation_id)
        result = await session.exec(statement)
        translation = result.first()
        return translation if translation is not None else None

    async def create_translation(
        self, translation_data: TranslationCreateModel, session: AsyncSession
    ):
        translation_data_dict = translation_data.model_dump()

        new_translation = Translations(**translation_data_dict)

        session.add(new_translation)

        await session.commit()

        return new_translation

    async def update_translation(
        self,
        translation_id: str,
        update_data: TranslationUpdateModel,
        session: AsyncSession,
    ):
        translation_to_update = self.get_translation(translation_id, session)

        if translation_to_update is not None:
            update_data_dict = update_data.model_dump()

            update_stmt = (
                update(Translations)
                .where(Translations.id == translation_id)
                .values(**update_data_dict)
            )
            await session.exec(update_stmt)
            await session.commit()

            return translation_to_update

        else:
            return None

    async def create_ai_translation(
        self,
        speech_info: YoutubeInfo,
        translation_request_data: TranslationCreateRequest,
        speakers: List[Speaker],
    ):
        ai_speech_data = AiTranslationCreateModel(
            transcript=translation_request_data.transcript,
            title=speech_info.title,
            speakers=speakers,
            speaker_number=len(speakers),
            context=translation_request_data.context,
        )

        # translate using ai service

        return await ai_service.translation_service(ai_speech_data)

    async def create_translation_with_ai_and_update_database(
        self, translation_request_data: TranslationCreateRequest, session: AsyncSession
    ):
        await update_english_summaries(translation_request_data)
        speakers: List[Speaker] = await speakers_for_ai_service(
            translation_request_data.speakers
        )
        speech_info: YoutubeInfo = await get_speech_info_from_url(
            translation_request_data.url
        )
        if speech_info.duration_in_seconds > 3600:
            raise Exception("The video is too long.")
        # create model for ai translation

        translation_result: AiTranslationServiceResultModel = (
            await self.create_ai_translation(
                speech_info, translation_request_data, speakers
            )
        )

        # create topics and people if needed, collect all topic and people ids to update the speech
        translation: Translations
        speech: Speeches
        new_translation, speech = await update_database_and_create_translation(
            translation_request_data, speech_info, translation_result, session
        )

        translation = await self.create_translation(new_translation, session)

        create_tts_audio_and_upload_to_s3(translation, translation_result)

        # update speech to include translation id and audio link
        await update_speech_with_audio_and_translation(speech, translation, session)

        return translation

    # async def create_brand_new_translation(self, translation_data: BrandNewTranslationUpdateModel, session: AsyncSession):
