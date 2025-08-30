#!/usr/bin/env python3
"""
Минимальный тестовый сервер для проверки работы роутера задач.
"""

import sys
import os

# Добавляем путь к проекту в sys.path
sys.path.append('/opt/feature-factory')

from fastapi import FastAPI
from app.api.tasks import router as tasks_router

app = FastAPI()

# Подключаем маршруты tasks
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["Tasks"])

@app.get("/")
def root():
    return {"message": "Test server for task trace API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8085)