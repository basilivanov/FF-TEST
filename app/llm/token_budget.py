#!/usr/bin/env python3
"""
Модуль для проверки бюджета токенов LLM.
"""

from app.llm.token_accountant import get_token_accountant

class WAIT_BUDGET(Exception):
    """Исключение, выбрасываемое при превышении бюджета токенов."""
    pass

class BudgetExceeded(Exception):
    """Исключение, выбрасываемое при превышении бюджета токенов."""
    pass

def check_role_budget(role: str, estimated_input_tokens: int):
    """
    Проверяет, не превышен ли бюджет токенов для роли.
    
    Args:
        role: Роль агента (Dev, QA, Scribe, Architect, Maintainer).
        estimated_input_tokens: Оценочное количество входных токенов.
        
    Raises:
        BudgetExceeded: Если бюджет превышен.
    """
    # Получаем экземпляр счетчика токенов
    token_accountant = get_token_accountant()
    
    # Оцениваем выходные токены (используем эвристику)
    estimated_output_tokens = max(50, int(estimated_input_tokens * 1.5))
    
    # Проверяем возможность расхода
    can_spend, remaining = token_accountant.can_spend(role, estimated_input_tokens, estimated_output_tokens)
    
    if not can_spend:
        raise BudgetExceeded(f"Budget exceeded for role {role}. Remaining tokens: {remaining}")