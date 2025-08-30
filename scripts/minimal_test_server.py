#!/usr/bin/env python3
"""
Минимальный рабочий пример для проверки регистрации эндпоинта.
"""

from fastapi import FastAPI
from pydantic import BaseModel

class SimpleResponse(BaseModel):
    message: str

app = FastAPI()

@app.get("/test")
async def simple_test():
    """
    Простой тестовый эндпоинт.
    """
    return {"message": "Simple test endpoint working"}

@app.get("/api/v1/tasks/{task_id}/trace")
async def task_trace(task_id: str):
    """
    Тестовый эндпоинт трассировки задачи.
    """
    return {
        "task_id": task_id,
        "items": [
            {
                "timestamp": "2025-08-30T11:00:09.700564",
                "kind": "task_started",
                "icon": "🧠",
                "title": "Задача запущена",
                "description": "Инициатор: Architect; контур: test",
                "severity": "info",
                "links": {
                    "log_id": "corr-c2915b40"
                },
                "details": {
                    "actor": "Architect",
                    "env": "test",
                    "correlation_id": "corr-c2915b40"
                }
            }
        ],
        "total": 1
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8085)