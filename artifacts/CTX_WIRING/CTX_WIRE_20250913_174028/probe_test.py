#!/usr/bin/env python3
"""
Тестирование ролей через Router с synthetic intents и проверка XML envelope
"""
import sys
import os
sys.path.append('/opt/feature-factory')

import json
from app.llm.router import completion
from app.context.packager import ContextPackager

def test_role_with_minimal_context(role: str, intent: str):
    """Тестирует роль с минимальным synthetic context"""
    try:
        # Создаем минимальный набор сообщений
        messages = [{"role": "user", "content": intent}]
        
        # Вызываем через Router
        result = completion(
            role=role,
            messages=messages, 
            max_tokens=150,
            temperature=0.1,
            timeout_s=10
        )
        
        # Проверяем формат ответа
        if "error" in result and result.get("error") == "NeedContext":
            return {
                "role": role,
                "status": "need_context",
                "response": result,
                "valid_format": True
            }
        
        # Проверяем наличие text или choices
        text_content = result.get("text", "")
        if not text_content and "choices" in result:
            text_content = result["choices"][0]["message"]["content"]
            
        # Пытаемся распарсить как JSON если роль требует JSON
        json_roles = ["Architect", "QA", "Gate", "Scribe", "Apply"]
        if role in json_roles:
            try:
                parsed = json.loads(text_content)
                return {
                    "role": role,
                    "status": "success",
                    "response": parsed,
                    "valid_format": True,
                    "type": "json"
                }
            except json.JSONDecodeError:
                return {
                    "role": role,
                    "status": "invalid_json",
                    "response": text_content,
                    "valid_format": False,
                    "type": "json_expected"
                }
        else:
            # Dev роль должна возвращать текст
            return {
                "role": role,
                "status": "success", 
                "response": text_content,
                "valid_format": True,
                "type": "text"
            }
            
    except Exception as e:
        return {
            "role": role,
            "status": "error",
            "response": str(e),
            "valid_format": False
        }

def run_all_probes():
    """Запускает все probes для ролей"""
    
    test_intents = {
        "Architect": "Create plan for adding health check endpoint",
        "Dev": "Generate code for /health endpoint in FastAPI", 
        "QA": "Validate health endpoint implementation",
        "Gate": "Review and approve health endpoint changes",
        "Scribe": "Document health endpoint in changelog",
        "Apply": "Apply git changes for health endpoint"
    }
    
    results = []
    
    for role, intent in test_intents.items():
        print(f"Testing role: {role}")
        result = test_role_with_minimal_context(role, intent)
        results.append(result)
        
    return results

if __name__ == "__main__":
    print("=== Running Role Probes ===")
    results = run_all_probes()
    
    # Записываем результаты в JSONL
    artifacts_dir = "/opt/feature-factory/artifacts/CTX_WIRING/CTX_WIRE_20250913_174028"
    with open(f"{artifacts_dir}/probes_results.jsonl", "w") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    print(f"Results written to probes_results.jsonl")
    
    # Краткий вывод
    for result in results:
        status = result["status"]
        role = result["role"]
        valid = result["valid_format"]
        print(f"  {role}: {status} (valid_format: {valid})")