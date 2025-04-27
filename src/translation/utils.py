from typing import List
from src.ai.schemas import Speaker
from src.translation.schemas import SpeakerInfo


async def speakers_for_ai_service(speakers_info: List[SpeakerInfo]):
    speakers = []
    for speaker_info in speakers_info:
        speakers.append(Speaker(name=speaker_info.name, info=speaker_info.info))
    return speakers
