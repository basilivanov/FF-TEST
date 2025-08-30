from fastapi import APIRouter, Query
from app.context.packager import ContextPackager

router = APIRouter()


@router.get("/")
def get_context(task_description: str = Query(..., description="Описание задачи для формирования контекста")):
    """Возвращает контекстный пакет для указанной задачи."""
    packager = ContextPackager()
    
    # Формируем структуру задачи для совместимости с существующим API
    task = {
        "id": "api_request",
        "feature_id": None,
        "role": "Dev",
        "dsl_json": {
            "description": task_description,
            "prompt": task_description
        }
    }
    
    context_pack = packager.build_context_for_task(task)
    
    return {"context_pack": context_pack}