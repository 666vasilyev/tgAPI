from fastapi import APIRouter, status
from fastapi.responses import FileResponse

from pathlib import Path

from src.utils.convert_to_excel import converting


router = APIRouter()

@router.post("/report", status_code=status.HTTP_200_OK)
async def generate_excel():
    # Вызываем функцию converting()
    await converting()
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