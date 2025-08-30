#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы API трассировки задачи.
"""

import sys
import os

# Добавляем путь к проекту в sys.path
sys.path.append('/opt/feature-factory')

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_task_trace():
    """Тестирует эндпоинт трассировки задачи."""
    response = client.get("/api/v1/tasks/test-task-1/trace")
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Task ID: {data.get('task_id')}")
        print(f"Total items: {data.get('total')}")
        print("First 3 items:")
        for i, item in enumerate(data.get('items', [])[:3]):
            print(f"  {i+1}. {item.get('title')} - {item.get('description')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_task_trace()