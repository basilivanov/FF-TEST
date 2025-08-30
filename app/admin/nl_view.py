#!/usr/bin/env python3
"""
NL (Natural Language) view for admin panel.
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from fastapi import HTTPException, status

router = APIRouter(prefix="/admin")

# Security
security = HTTPBasic()

# Для простоты используем Jinja2 templates
templates = Jinja2Templates(directory="app/admin/templates")

def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify basic auth credentials."""
    # В реальной реализации здесь должна быть проверка с БД или env vars
    # Для демонстрации используем простую проверку
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "password")
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

class NLProcessor:
    """Process natural language input to generate intent and DAG."""
    
    @staticmethod
    def process_nl_input(text: str) -> dict:
        """
        Process natural language input and return intent and DAG.
        This is a simplified version - in real implementation this would call Maintainer LLM.
        """
        # Простая эвристика для определения intent
        text_lower = text.lower()
        
        if "работ" in text_lower or "job" in text_lower:
            intent = "status_jobs"
            slots = {}
        elif "лог" in text_lower or "log" in text_lower:
            intent = "logs_tail"
            slots = {"last": 100}
        elif "документ" in text_lower or "doc" in text_lower:
            intent = "docs_status"
            slots = {}
        else:
            intent = "unknown"
            slots = {}
        
        return {
            "intent": intent,
            "env": "test",
            "slots": slots
        }
    
    @staticmethod
    def generate_dag(intent_data: dict) -> list:
        """
        Generate DAG based on intent.
        This is a simplified version - in real implementation this would call Architect.
        """
        intent = intent_data.get("intent", "unknown")
        
        if intent == "status_jobs":
            return [
                {
                    "id": "check_jobs_status",
                    "name": "Проверка статуса задач",
                    "kind": "job",
                    "role": "Dev",
                    "preconditions": [],
                    "postconditions": ["jobs_status_checked"],
                    "idempotency_key": "jobs_status_v1",
                    "retry": {"max": 2, "backoff": "exp:5,30,120"},
                    "deadline": "PT5M",
                    "models": ["flash"],
                    "outputs": ["logs"],
                    "dod": ["статус задач отображен"],
                    "severity": "low"
                }
            ]
        elif intent == "logs_tail":
            return [
                {
                    "id": "fetch_recent_logs",
                    "name": "Получение последних логов",
                    "kind": "job",
                    "role": "Dev",
                    "preconditions": [],
                    "postconditions": ["recent_logs_fetched"],
                    "idempotency_key": "logs_tail_v1",
                    "retry": {"max": 2, "backoff": "exp:5,30,120"},
                    "deadline": "PT5M",
                    "models": ["flash"],
                    "outputs": ["logs"],
                    "dod": ["логи отображены"],
                    "severity": "low"
                }
            ]
        elif intent == "docs_status":
            return [
                {
                    "id": "check_docs_status",
                    "name": "Проверка статуса документов",
                    "kind": "doc",
                    "role": "Scribe",
                    "preconditions": [],
                    "postconditions": ["docs_status_checked"],
                    "idempotency_key": "docs_status_v1",
                    "retry": {"max": 2, "backoff": "exp:5,30,120"},
                    "deadline": "PT5M",
                    "models": ["flash"],
                    "outputs": ["files"],
                    "dod": ["статус документов отображен"],
                    "severity": "low"
                }
            ]
        else:
            return [
                {
                    "id": "unknown_intent",
                    "name": "Неизвестный intent",
                    "kind": "job",
                    "role": "Dev",
                    "preconditions": [],
                    "postconditions": ["intent_processed"],
                    "idempotency_key": "unknown_intent_v1",
                    "retry": {"max": 1, "backoff": "lin:10,20"},
                    "deadline": "PT5M",
                    "models": ["flash"],
                    "outputs": ["logs"],
                    "dod": ["intent обработан"],
                    "severity": "low"
                }
            ]

@router.get("/nl", response_class=HTMLResponse)
async def nl_form(request: Request, username: str = Depends(get_current_username)):
    """Render NL input form."""
    return templates.TemplateResponse("nl_form.html", {"request": request})

@router.post("/nl/process")
async def process_nl(text: str = Form(...), username: str = Depends(get_current_username)):
    """Process NL input and return intent and DAG."""
    # Process the natural language input
    intent_data = NLProcessor.process_nl_input(text)
    
    # Generate DAG
    dag = NLProcessor.generate_dag(intent_data)
    
    return {
        "intent": intent_data,
        "dag": dag,
        "message": "Intent и DAG сгенерированы (не выполняются)"
    }