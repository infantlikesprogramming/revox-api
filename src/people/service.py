from sqlmodel.ext.asyncio.session import AsyncSession
from .schemas import PersonCreateModel, PersonUpdateModel
from sqlmodel import select, desc, update
from src.db.models import People
from datetime import datetime


class PersonService:
    async def get_person(self, person_id, session: AsyncSession):
        statement = select(People).where(People.id == person_id)
        result = await session.exec(statement)
        person = result.first()
        return person if person is not None else None

    async def create_person(
        self, person_data: PersonCreateModel, session: AsyncSession
    ):
        person_data_dict = person_data.model_dump()

        new_person = People(**person_data_dict)

        session.add(new_person)

        await session.commit()

        return new_person

    async def update_person(
        self, person_id: str, update_data: PersonUpdateModel, session: AsyncSession
    ):
        person_to_update = self.get_person(person_id, session)

        if person_to_update is not None:
            update_data_dict = update_data.model_dump()
            update_stmt = (
                update(People).where(People.id == person_id).values(**update_data_dict)
            )
            await session.exec(update_stmt)
            await session.commit()
            await session.commit()

            return person_to_update

        else:
            return None
