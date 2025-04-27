from fastapi import APIRouter, status, Depends, BackgroundTasks
from fastapi.exceptions import HTTPException
from src.translation.schemas import TranslationCreateRequest, Translation
from pathlib import Path
from sqlmodel import select, desc
from src.db.main import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from fastapi.responses import FileResponse
from datetime import datetime
from .service import TranslationService
from src.ai.schemas import AiTranslationServiceResultModel
from src.ai.service import AiService
from src.utils import get_speech_info_from_url, YoutubeInfo

translation_router = APIRouter()
translation_service = TranslationService()


@translation_router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_a_translation(
    translation_data: TranslationCreateRequest,
    bg_task: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> dict:
    speech_info: YoutubeInfo = await get_speech_info_from_url(translation_data.url)
    if speech_info.duration_in_seconds > 3600:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "The video is too long."},
        )
    bg_task.add_task(
        translation_service.create_translation_and_update_database,
        translation_data,
        session,
    )

    return {"message": "Thank you. Your request has been received"}


# class Res(BaseModel):
#     message: str


# @translation_router.get("/", status_code=status.HTTP_200_OK, response_model=Res)
# async def database_go(session: AsyncSession = Depends(get_session)):

#     new_speech = Speeches(
#         title="Bài diễn văn tốt nghiệp năm 2024 của CEO NVIDIA Jensen Huang tại Caltech",
#         topic_name="Trí Tuệ Nhân Tạo",
#         topic_ids=["896d23fd-c814-469a-ba86-09ae7cf4961e"],
#         people_ids=["f778ad83-3c8a-499c-a1e2-fec5e2b2a57a"],
#         source_image="/icons/youtube.png",
#         source_url="https://www.youtube.com/watch?v=53iujxhGRsE&t=668s",
#         source_owner="9696-official",
#         language="Tiếng Anh",
#         duration="30:20",
#         audio_url="/audio/Bài diễn văn tốt nghiệp năm 2024 của CEO NVIDIA Jensen Huang tại Caltech.mp3",
#         speech_summary="Jensen Huang khuyên sinh viên Caltech 2024 tin tưởng vào ý tưởng đột phá, kiên trì và học từ thất bại. Ông nhấn mạnh sức mạnh của AI, kể về hành trình Nvidia, và giá trị của sự kiên trì. Huang khuyên tìm nghề nghiệp để cống hiến, ưu tiên cuộc sống, và coi thất bại là cơ hội, nhấn mạnh sự kiên trì và tập trung.",
#         translation_id=[],
#         cover_url="/scimages/jshuang.jpg",
#     )

#     new_speech.publish_date = datetime.strptime("2024-7-1", "%Y-%m-%d")

#     print(new_speech)

#     session.add(new_speech)

#     await session.commit()

#     return Res(message="all done!")


# @translation_router.get(
#     "/translation", status_code=status.HTTP_200_OK, response_model=Res
# )
# async def database_go_topic(session: AsyncSession = Depends(get_session)):

#     # new_speech = People(
#     #     person_name="Lê Viết Quốc",
#     #     organization="Google Brain",
#     #     person_image="/scimages/personImages/lvq.jpg",
#     #     short_summary="Quốc V. Lê, là đồng sáng lập Google Brain, tiên phong seq2seq, doc2vec, AutoML.",
#     #     long_summary="Quoc Le là một nhà nghiên cứu trí tuệ nhân tạo (AI) người Mỹ gốc Việt, nổi tiếng với công việc tại Google Brain. Ông đóng vai trò quan trọng trong việc phát triển các mô hình học sâu và máy học, giúp thúc đẩy sự phát triển của AI hiện đại. Một trong những đóng góp lớn nhất của ông là đồng sáng tạo phương pháp học chuỗi-đến-chuỗi, giúp cải thiện dịch máy. Ông cũng tham gia phát triển AutoML, giúp tự động hóa quá trình tạo mô hình AI. Những nghiên cứu của ông đang định hình tương lai của AI, làm cho công nghệ này trở nên mạnh mẽ và dễ tiếp cận hơn.",
#     #     speechesId=[],
#     # )

#     # statement = select(People).where(
#     #     People.id == "f778ad83-3c8a-499c-a1e2-fec5e2b2a57a"
#     # )
#     # result = await session.exec(statement)

#     # person_to_update = result.first()
#     # if person_to_update is not None:
#     #     setattr(
#     #         person_to_update,
#     #         "speeches_id",
#     #         person_to_update.speeches_id.append("47ba036f-0781-43dc-9216-3fe6ddb9aab4"),
#     #     )

#     # await session.commit()

#     # statement = select(Speeches).where(
#     #     Speeches.id == "47ba036f-0781-43dc-9216-3fe6ddb9aab4"
#     # )
#     # result = await session.exec(statement)

#     # speech_to_update = result.first()
#     # if speech_to_update is not None:
#     #     setattr(
#     #         speech_to_update,
#     #         "topic_ids",
#     #         speech_to_update.topic_ids.append("18ff2654-d2a8-44ff-b4f5-c931d1271407"),
#     #     )

#     # await session.commit()

#     # print(new_speech)

#     # session.add(new_speech)

#     # await session.commit()

#     new_translation = Translations(
#         speech_id="47ba036f-0781-43dc-9216-3fe6ddb9aab4",
#         original="hello",
#         translation="xin chao",
#     )

#     session.add(new_translation)

#     await session.commit()

#     return Res(message=str(new_translation.id))


# @translation_router.get(
#     "/audio/{file_name}", status_code=status.HTTP_200_OK, response_model=None
# )
# async def get_translation_audio(file_name: str):
#     base_dir = Path(__file__).parent  # Directory of the script
#     file_path = base_dir / file_name
#     return FileResponse(
#         path=file_path, filename=file_name, media_type="application/octet-stream"
#     )
