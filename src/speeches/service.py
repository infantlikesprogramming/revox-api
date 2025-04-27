from sqlmodel.ext.asyncio.session import AsyncSession

# from .schemas
from sqlmodel import select, desc, update
from src.db.models import Speeches
from datetime import datetime
from .schemas import SpeechCreateModel, SpeechUpdateModel, Speech


class SpeechService:
    async def get_speech(self, speech_id, session: AsyncSession):
        statement = select(Speeches).where(Speeches.id == speech_id)
        result = await session.exec(statement)
        speech = result.first()
        return speech if speech is not None else None

    async def update_speech(
        self, speech_id: str, update_data: SpeechUpdateModel, session: AsyncSession
    ):
        speech_to_update = await self.get_speech(speech_id, session)

        if speech_to_update is not None:
            update_data_dict = update_data.model_dump()
            update_stmt = (
                update(Speeches)
                .where(Speeches.id == speech_id)
                .values(**update_data_dict)
            )
            await session.exec(update_stmt)
            await session.commit()
            return speech_to_update
        else:
            return None

    async def createSpeech(self, speech_data: SpeechCreateModel, session: AsyncSession):
        speech_data_dict = speech_data.model_dump()

        new_speech = Speeches(**speech_data_dict)

        new_speech.publish_date = datetime.strptime(
            speech_data_dict["publish_date"], "%Y-%m-%d"
        )

        session.add(new_speech)

        await session.commit()

        return new_speech
