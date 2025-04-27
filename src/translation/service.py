from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import (
    TranslationCreateModel,
    TranslationUpdateModel,
    TranslationCreateRequest,
    BrandNewTranslationUpdateModel,
    SpeakerInfo,
    YoutubeInfo,
)
from concurrent.futures import ProcessPoolExecutor
from src.ai.schemas import (
    AiTranslationServiceResultModel,
    AiTranslationCreateModel,
    Speaker,
    TtsCreateModel,
)
from src.topic.schemas import TopicCreateModel
from src.people.schemas import PersonUpdateModel, PersonCreateModel

from src.speeches.schemas import SpeechCreateModel, SpeechUpdateModel
from src.ai.service import AiService
from typing import Optional, Dict, List
from sqlmodel import select, desc, update
from src.db.models import Translations, Topics, People, Speeches
from datetime import datetime
from .utils import speakers_for_ai_service
from src.utils import (
    get_speech_info_from_url,
    file_to_s3,
    merge_mp3_files,
    YoutubeInfoResponse,
)
from src.topic.service import TopicService
from src.people.service import PersonService
from src.speeches.service import SpeechService
from dotenv import load_dotenv
import os

topic_service = TopicService()
person_service = PersonService()
speech_service = SpeechService()
ai_service = AiService()

load_dotenv
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
            await session.commit()

            return translation_to_update

        else:
            return None

    async def create_translation_and_update_database(
        self, translation_request_data: TranslationCreateRequest, session: AsyncSession
    ):
        speakers: Speaker = await speakers_for_ai_service(
            translation_request_data.speakers
        )
        speech_info: YoutubeInfo = await get_speech_info_from_url(
            translation_request_data.url
        )
        if speech_info.duration_in_seconds > 3600:
            raise Exception("The video is too long.")
        # create model for ai translation
        ai_speech_data = AiTranslationCreateModel(
            transcript=translation_request_data.transcript,
            title=speech_info.title,
            speakers=speakers,
            speaker_number=len(speakers),
            context=translation_request_data.context,
        )

        # translate using ai service
        translation_result: AiTranslationServiceResultModel = (
            await ai_service.translation_service(ai_speech_data)
        )

        # create topics and people if needed, collect all topic and people ids to update the speech
        allTopicsIds = []
        allPeopleIds = []

        for topic in translation_request_data.topics:
            if topic.create == True:
                new_topic = TopicCreateModel(
                    topic_name=topic.name, topic_image=topic.topic_image
                )
                allTopicsIds.append(
                    (await topic_service.create_topic(new_topic, session)).id
                )
            else:
                allTopicsIds.append(topic.id)

        for person in translation_request_data.speakers:
            if person.create == True:
                new_person = PersonCreateModel(
                    person_name=person.name,
                    organization=person.org,
                    person_image=person.person_image,
                    short_summary=person.short_summary,
                    long_summary=person.long_summary,
                    speeches_id=[],
                )
                allPeopleIds.append(
                    (await person_service.create_person(new_person, session)).id
                )
            else:
                allPeopleIds.append(person.id)

        speech = None

        # create speech for translation
        if translation_request_data.createSpeech == True:
            new_speech = SpeechCreateModel(
                title=speech_info.title,
                topic_name=translation_request_data.topics[0].name,
                topic_ids=allTopicsIds,
                people_ids=allPeopleIds,
                source_image="/icons/youtube.png",
                source_url=translation_request_data.url,
                source_owner=speech_info.uploader,
                language=speech_info.language,
                duration=speech_info.duration,
                audio_url="Unknown",
                speech_summary=translation_result.ai_response.summary_in_vietnamese,
                translation_id=[],
                cover_url=translation_request_data.cover_url,
                publish_date=speech_info.publish_date,
            )

            speech = await speech_service.createSpeech(new_speech, session)
        else:
            speech = await speech_service.get_speech(
                translation_request_data.speech_id, session
            )

        # create a new translation
        new_translation = TranslationCreateModel(
            speech_id=speech.id,
            original=translation_result.attributed_speech,
            translation=translation_result.translated_speech,
        )

        translation = await self.create_translation(new_translation, session)

        audiopath = f"src/translation/audio/{translation.id}.mp3"
        # async_audio_functions = []
        tts_datas = []
        # # create audio for translation
        for i in range(len(translation_result.translated_speech_for_tts)):
            tts_data = TtsCreateModel(
                speech_transcript=translation_result.translated_speech_for_tts[i],
                filepath=f"src/translation/audio/a{i}",
            )
            tts_datas.append(tts_data)
            # async_audio_functions.append(ai_service.tts_service)

        # # Create coroutine objects by calling each function
        # coroutines = [
        #     func(tts_datas[i]) for i, func in enumerate(async_audio_functions)
        # ]

        # # Pass coroutines to gather
        # results = await asyncio.gather(*coroutines)
        results = []
        with ProcessPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(ai_service.tts_service, data) for data in tts_datas
            ]
            for future in futures:
                results.append(future.result())

        merge_mp3_files(results, audiopath)

        file_to_s3(audiopath)

        os.remove(audiopath)
        for part_audios in results:
            os.remove(part_audios)

        # update speech to include translation id and audio link
        speech.translation_id.append(translation.id)

        speech_update_data = SpeechUpdateModel(
            title=speech.title,
            topic_name=speech.topic_name,
            topic_ids=speech.topic_ids,
            people_ids=speech.people_ids,
            source_image=speech.source_image,
            publish_date=speech.publish_date.strftime("%Y-%m-%d"),
            source_owner=speech.source_owner,
            language=speech.language,
            duration=speech.duration,
            audio_url=f"{cloudfront_url}/{translation.id}.mp3",
            speech_summary=speech.speech_summary,
            cover_url=speech.cover_url,
            translation_id=speech.translation_id,
        )

        await speech_service.update_speech(speech.id, speech_update_data, session)

        return translation

    #     speakers: List[Speaker]
    # url: str
    # context: Optional[str] = None
    # topicName: str
    # topicId: List[str]

    # async def create_brand_new_translation(self, translation_data: BrandNewTranslationUpdateModel, session: AsyncSession):
