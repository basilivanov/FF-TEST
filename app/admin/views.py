#!/usr/bin/env python3
"""
Views for admin panel.
"""

from sqladmin import ModelView
from sqlalchemy import create_engine, MetaData, Table

# Создаем engine и подключаемся к БД
DATABASE_URL = "sqlite:////opt/feature-factory/data/test.db"
engine = create_engine(DATABASE_URL)

# Создаем metadata и загружаем таблицы
metadata = MetaData()

try:
    metadata.reflect(bind=engine)
    
    # Получаем таблицы если они существуют
    if 'jobs' in metadata.tables:
        jobs = metadata.tables['jobs']
    else:
        jobs = None
        
    if 'doc_registry' in metadata.tables:
        doc_registry = metadata.tables['doc_registry']
    else:
        doc_registry = None
        
    if 'agent_events' in metadata.tables:
        agent_events = metadata.tables['agent_events']
    else:
        agent_events = None

    # Создаем views только если таблицы существуют
    if jobs is not None:
        class JobView(ModelView, model=jobs):
            column_list = ["id", "name", "status", "started_at", "finished_at"]
            column_searchable_list = ["name"]
            column_sortable_list = ["id", "started_at", "finished_at"]
            column_default_sort = [("id", True)]
            name = "Job"
            name_plural = "Jobs"
            icon = "fas fa-tasks"
    else:
        JobView = None

    if doc_registry is not None:
        class DocRegistryView(ModelView, model=doc_registry):
            column_list = ["doc_name", "version", "updated_at"]
            column_searchable_list = ["doc_name"]
            column_sortable_list = ["updated_at"]
            name = "Document"
            name_plural = "Documents"
            icon = "fas fa-file-alt"
    else:
        DocRegistryView = None

    if agent_events is not None:
        class AgentEventView(ModelView, model=agent_events):
            column_list = ["id", "ts", "agent_role", "event"]
            column_searchable_list = ["agent_role", "event"]
            column_sortable_list = ["ts", "id"]
            column_default_sort = [("ts", True)]
            name = "Agent Event"
            name_plural = "Agent Events"
            icon = "fas fa-history"
    else:
        AgentEventView = None

except Exception as e:
    print(f"Warning: Could not initialize admin views: {e}")
    JobView = None
    DocRegistryView = None
    AgentEventView = None