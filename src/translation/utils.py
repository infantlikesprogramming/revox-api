from typing import List
from src.ai.schemas import (
    Speaker,
    AiSpeakerServiceSpeakersDetails,
    AiSpeakerServiceSpeaker,
)
from src.translation.schemas import (
    SpeakerInfo,
    TranslationCreateRequest,
    YoutubeInfo,
    TranslationCreateModel,
    AiTranslationServiceResultModel,
)
from src.topic.schemas import TopicCreateModel
from src.speeches.schemas import SpeechCreateModel, SpeechUpdateModel
from src.people.schemas import PersonCreateModel
from src.ai.schemas import TtsCreateModel
from src.db.models import Translations, Speeches
from src.utils import merge_mp3_files, file_to_s3
import os
from dotenv import load_dotenv
from sqlmodel.ext.asyncio.session import AsyncSession
from src.ai.service import AiService
from src.topic.service import TopicService
from src.people.service import PersonService
from src.speeches.service import SpeechService
from concurrent.futures import ProcessPoolExecutor

topic_service = TopicService()
person_service = PersonService()
speech_service = SpeechService()
ai_service = AiService()
load_dotenv()
cloudfront_url = os.environ.get("CLOUDFRONT_URL")


async def update_english_summaries(translation_request_data: TranslationCreateRequest):
    speakers = translation_request_data.speakers
    for speaker in speakers:
        if speaker.create == True:
            speaker_for_ai_service = AiSpeakerServiceSpeaker(
                name=speaker.name,
                organization=speaker.org,
                extra_information=speaker.long_summary,
            )

            speaker_details_for_ai_service = AiSpeakerServiceSpeakersDetails(
                speakers=[speaker_for_ai_service],
                number_of_speakers=1,
            )
            english_summary = (
                (
                    await ai_service.speaker_service(
                        speakers=speaker_details_for_ai_service, language="English"
                    )
                )
                .speaker_summaries[0]
                .speaker_long_summary
            )
            speaker.english_summary = english_summary


async def speakers_for_ai_service(speakers_info: List[SpeakerInfo]):
    speakers = []
    for speaker_info in speakers_info:
        info = speaker_info.english_summary
        speakers.append(Speaker(name=speaker_info.name, info=info))
    return speakers


async def update_database_and_create_translation(
    translation_request_data: TranslationCreateRequest,
    speech_info: YoutubeInfo,
    translation_result: AiTranslationServiceResultModel,
    session: AsyncSession,
) -> Translations:
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
                english_summary=person.english_summary,
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
            vi_title=translation_result.ai_response.short_title,
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

    return [new_translation, speech]


def create_tts_audio_and_upload_to_s3(
    translation: Translations,
    translation_result: AiTranslationServiceResultModel,
):
    audiopath = f"src/translation/audio/{translation.id}.mp3"
    # async_audio_functions = []
    tts_datas = []
    # # create audio for translation
    for i in range(len(translation_result.translated_speech_for_tts)):
        tts_data = TtsCreateModel(
            speech_transcript=translation_result.translated_speech_for_tts[i],
            filepath=f"src/translation/audio/a{i}",
            voice=translation_result.ai_response.voice_for_tts,
        )
        tts_datas.append(tts_data)

    results = []
    with ProcessPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(ai_service.tts_service, data) for data in tts_datas]
        for future in futures:
            results.append(future.result())

    merge_mp3_files(results, audiopath)

    file_to_s3(audiopath)

    os.remove(audiopath)
    for part_audios in results:
        os.remove(part_audios)


async def update_speech_with_audio_and_translation(
    speech: Speeches,
    translation: Translations,
    session: AsyncSession,
):
    speech.translation_id.append(translation.id)

    speech_update_data = SpeechUpdateModel(
        title=speech.title,
        vi_title=speech.vi_title,
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
