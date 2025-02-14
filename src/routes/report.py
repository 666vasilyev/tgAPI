from fastapi import APIRouter, status, Depends
from fastapi.responses import FileResponse

from pathlib import Path

from src.utils.convert_to_excel import converting
from src.dependencies import get_db, get_channel_repository, get_post_repository, get_comment_repository
from src.repositories.channel import ChannelRepository
from src.repositories.post import PostRepository
from src.repositories.comment import CommentRepository

router = APIRouter()

@router.post("/report", status_code=status.HTTP_200_OK)
async def generate_excel(
        channel_repo: ChannelRepository = Depends(get_channel_repository),
        post_repo: PostRepository = Depends(get_post_repository),
        comment_repo: CommentRepository = Depends(get_comment_repository),
):
    # Вызываем функцию converting()
    await converting(
        channel_repo,
        post_repo,
        comment_repo
    )
    return 'Successfully created excel report'
    # После завершения функции, отправляем пользователю файл output.xlsx
    


@router.get("/report", status_code=status.HTTP_200_OK)
async def get_excel():
    # Укажите путь к файлу "output.xlsx"
    file_path = Path(__file__).resolve().parent / "output.xlsx"
    if file_path.exists():
        return FileResponse(file_path, filename="output.xlsx")
    else:
        return {"error": "Файл не найден"}