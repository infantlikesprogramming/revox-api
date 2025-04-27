from pydantic import BaseModel, Field
from typing import List, Optional
import uuid


class Speaker(BaseModel):
    name: str
    info: str


class SpeechDetails(BaseModel):
    title: str
    stype: Optional[str] = None
    speakers: List[Speaker]
    number_of_speakers: int
    context: Optional[str] = None


class AiTranslationCreateModel(BaseModel):
    transcript: str
    title: str
    speakers: List[Speaker]
    speaker_number: int
    context: Optional[str] = None


class Segment(BaseModel):
    segment_order_id: int
    speaker_name: str
    original_speech: str
    translation_vi: str = Field(
        description="full translation of the original speech into vietnamese. As detailed as possible, filler words are obmitted, add punctuations if needed to make grammatical sentences."
    )


class AiTranslationResponseModel(BaseModel):
    speaker_attribution: List[Segment] = Field(
        description="Each segment contain the name and speech content of the attributed speaker. The length of the original content of the segment should be below 3800 characters and can be much lower if needed."
    )
    summary_in_vietnamese: str = Field(
        description="Text in Vietnamese",
        max_length=900,
    )
    short_title: str = Field(
        description="AI generated short title, at most 20 character's long",
        max_length=120,
    )
    needs_escalation: bool
    follow_up_required: bool
    original_language: str = Field(
        description="Language of the original speech transcript"
    )
    sentiment: str = Field(
        description="overall sentiment of the transcript", max_length=20
    )
    cost_of_service: Optional[str] = Field(
        description="amount in $ that the AI service cost"
    )
    voice_for_tts: str = Field(
        description="Based on the sentiment, pick one of the voices from OpenAI api for text-to-speech. Return result in one word, lowercased. If unable to point to the exact voice, return an empty string"
    )
    what_to_notice_for_the_request: Optional[str] = Field(
        description="If you the agent wants to provide some context for the next request I send you, record it here."
    )
    chatbot_message: Optional[str] = Field(
        description="In case your response does not match this return model, return the reason why here, and comply to the type of the other fields"
    )


class AiTranslationServiceResultModel(BaseModel):
    ai_response: AiTranslationResponseModel
    attributed_speech: str
    translated_speech: str
    translated_speech_for_tts: List[str]


class TtsCreateModel(BaseModel):
    speech_transcript: str
    filepath: str
    voice: str = "nova"


class AiSpeakerServiceSpeakerInformation(BaseModel):
    speaker_name: str
    speaker_long_summary: str = Field(
        description="Detailed summary of the speaker, in the requested language",
        max_length=900,
    )
    speaker_short_summary: str = Field(
        description="Brief summary of the speaker, preferably 2 sentences, in the requested language",
        max_length=150,
    )


class AiSpeakerServiceResponseModel(BaseModel):
    speaker_summaries: List[AiSpeakerServiceSpeakerInformation]
    needs_escalation: bool
    follow_up_required: bool
    cost_of_this_query_in_dollars: float


class AiSpeakerServiceSpeaker(BaseModel):
    name: str
    organization: str
    extra_information: Optional[str] = None


class AiSpeakerServiceSpeakersDetails(BaseModel):
    speakers: List[AiSpeakerServiceSpeaker]
    number_of_speakers: int


class AiSpeakerServiceSpeakersRequest(BaseModel):
    speakers: List[AiSpeakerServiceSpeaker]
