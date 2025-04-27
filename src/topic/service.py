from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import TopicCreateModel, TopicUpdateModel
from sqlmodel import select, desc, update
from src.db.models import Topics
from datetime import datetime


class TopicService:
    async def get_topic(self, topic_id, session: AsyncSession):
        statement = select(Topics).where(Topics.id == topic_id)
        result = await session.exec(statement)
        topic = result.first()
        return topic if topic is not None else None

    async def create_topic(self, topic_data: TopicCreateModel, session: AsyncSession):
        topic_data_dict = topic_data.model_dump()

        new_topic = Topics(**topic_data_dict)

        session.add(new_topic)

        await session.commit()

        return new_topic

    async def update_topic(
        self, topic_id: str, update_data: TopicUpdateModel, session: AsyncSession
    ):
        topic_to_update = self.get_topic(topic_id, session)

        if topic_to_update is not None:
            update_data_dict = update_data.model_dump()
            update_stmt = (
                update(Topics).where(Topics.id == topic_id).values(**update_data_dict)
            )
            await session.exec(update_stmt)
            await session.commit()
            await session.commit()

            return topic_to_update

        else:
            return None
