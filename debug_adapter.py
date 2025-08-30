#!/usr/bin/env python3

# Тестируем какой адаптер используется
from app.llm.session_manager import LLMSessionManager

manager = LLMSessionManager()

# Тестируем получение адаптера для anthropic_opus41
adapter = manager.get_llm_adapter("test_session", "Maintainer")
print(f"Adapter type: {type(adapter)}")
print(f"Adapter name: {adapter.provider_name}")

# Тестируем build_cmd
try:
    messages = [{"role": "user", "content": "test"}]
    cmd, env, input_data = adapter.build_cmd(messages, 100, 0.3)
    print(f"Command: {cmd}")
except Exception as e:
    print(f"Error in build_cmd: {e}")