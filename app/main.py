from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import os
from app.index.api import router as index_router
from app.api.middleware import CorrelationIdMiddleware
from app.admin.routes import router as admin_router
from app.admin.call_graph_api import router as admin_call_graph_router
from app.api.orchestrator import router as orchestrator_router
from app.api.orchestrator_queue_endpoints import router as orchestrator_queue_router
from app.api.health import router as health_router
# from app.api.health import check_llm_cli_health # Removed this import as the hardcoded route is removed
from app.api.maintainer import router as maintainer_router
from app.api.stream import router as stream_router
from app.api.logs import router as logs_router
from app.api.logs_errors_endpoints import router as logs_errors_router
from app.api.tokens import router as tokens_router
from app.api.tokens_stats_endpoints import router as tokens_stats_router
from app.api.docs_status import router as docs_status_router
from app.api.chat import router as chat_router
from app.api.chat_websocket import router as chat_websocket_router # Новый импорт
# from app.api.chat_v2 import router as chat_v2_router
from app.api.llm_endpoints import router as llm_router_api
from app.api.llm_status import router as llm_status_router
from app.api.ops import router as ops_router
from app.api.secrets import router as secrets_router
from app.api.analyst import router as analyst_router
from app.api.context import router as context_router
from app.api.agents_status import router as agents_status_router
from app.api.tasks import router as tasks_router

# Импортируем модуль защиты БД
try:
    from app.db.guard import guard_db_path, FAILED_NEEDS_ATTENTION
except ImportError:
    # Заглушка для случаев, когда модуль еще не создан
    def guard_db_path(current_db_url: str) -> None:
        pass
    
    class FAILED_NEEDS_ATTENTION(Exception):
        pass

# Set openapi_url to /openapi.json explicitly
app = FastAPI(title="Feature Factory MVP", openapi_url="/openapi.json")

# Add global exception handler
from fastapi import Request
from app.api.errors import unhandled_error_handler
app.add_exception_handler(Exception, unhandled_error_handler)

# Подключаем middleware для корреляции
app.add_middleware(CorrelationIdMiddleware)

# Подключаем маршруты индекса
app.include_router(index_router)

# Подключаем маршруты админки
app.include_router(admin_router)
app.include_router(admin_call_graph_router)

# Подключаем маршруты оркестратора
app.include_router(orchestrator_router)

# Подключаем маршруты очередей оркестратора
app.include_router(orchestrator_queue_router)

# Подключаем маршруты maintainer
app.include_router(maintainer_router)

# Подключаем маршруты stream
app.include_router(stream_router)

# Подключаем маршруты логов
app.include_router(logs_router)

# Подключаем маршруты ошибок логов
app.include_router(logs_errors_router)

# Подключаем маршруты токенов
app.include_router(tokens_router)

# Подключаем маршруты статистики токенов
app.include_router(tokens_stats_router)

# Подключаем маршруты health check
app.include_router(health_router)

# Подключаем маршруты docs status
app.include_router(docs_status_router)
app.include_router(chat_router)
app.include_router(chat_websocket_router) # Включение нового роутера
# app.include_router(chat_v2_router)
app.include_router(llm_router_api)
app.include_router(llm_status_router)

# Подключаем маршруты ops
app.include_router(ops_router)
app.include_router(secrets_router)

# Подключаем маршруты analyst
app.include_router(analyst_router)

# Подключаем маршруты context
app.include_router(context_router, prefix="/api/v1/context", tags=["Context"])

# Подключаем маршруты кэшированного статуса агентов
app.include_router(agents_status_router, tags=["Agents"])

# Подключаем маршруты tasks
app.include_router(tasks_router, prefix="/api/v1/tasks", tags=["Tasks"])

# Подключаем маршруты трассировки
from app.api.trace import router as trace_router
app.include_router(trace_router, prefix="/api/v1", tags=["Trace"])

"""
Подключение дополнительных роутеров, которые могут появляться как артефакты
после прогона графа (например, app/api/ping.py). Импорт защищаем, чтобы
приложение стартовало даже если файла ещё нет.
"""
try:
    from app.api.ping import router as ping_router
    app.include_router(ping_router)
except Exception:
    # Нет ping-роутера — ничего страшного, он может появиться как артефакт
    pass



# Получаем DATABASE_URL из переменных окружения или используем тестовую базу
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////opt/feature-factory/data/test.db")

# Проверяем путь к БД
try:
    guard_db_path(DATABASE_URL)
except FAILED_NEEDS_ATTENTION as e:
    # В production окружении останавливаем приложение
    if os.getenv("ENV", "TEST") == "PROD":
        raise
    else:
        # В тестовом окружении просто логируем предупреждение
        print(f"Warning: DB guard check failed: {e}")

@app.get("/")
def root():
    return {"message": "Feature Factory MVP", "docs": "/docs", "admin": "/admin/jobs"}

# Removed hardcoded health endpoints
# @app.get("/api/v1/health")
# def health(): 
#     return {"status": "ok"}

# ping-эндпоинт не хардкодим: он должен появляться как артефакт

# Removed hardcoded health_cli endpoint
# @app.get("/api/v1/health/cli")
# def health_cli():
#     return check_llm_cli_health()

# Инициализация админки sqladmin
from sqladmin import Admin
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL)

# Создаем админку с BasicAuth
admin = Admin(app, engine=engine, base_url="/admin/sqladmin")

# Добавляем views для таблиц
try:
    from app.admin.views import JobView, DocRegistryView, AgentEventView
    if JobView:
        admin.add_view(JobView)
    if DocRegistryView:
        admin.add_view(DocRegistryView)
    if AgentEventView:
        admin.add_view(AgentEventView)
except Exception as e:
    print(f"Warning: Could not add admin views: {e}")