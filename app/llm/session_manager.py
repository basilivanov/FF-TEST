from typing import Dict, Any
import time
import yaml
import structlog

# Настройка логгера
logger = structlog.get_logger()

# Путь к конфигурационному файлу роутинга
ROUTING_CONFIG_PATH = "/opt/feature-factory/configs/llm_routing.yaml"

class LLMSessionManager:
    _instance = None
    _active_llm_instances: Dict[str, Dict[str, Any]] = {} # {session_id: {role: LLM_adapter}}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMSessionManager, cls).__new__(cls)
        return cls._instance

    def get_llm_adapter(self, session_id: str, role: str) -> Any:
        """
        Возвращает или создает LLM-адаптер для данной сессии и роли.
        Если session_id is None, создает временный адаптер без сохранения.
        """
        # Если session_id не передан, создаем временный адаптер
        if session_id is None:
            return self._create_new_adapter(role)
            
        if session_id not in self._active_llm_instances:
            self._active_llm_instances[session_id] = {}

        if role not in self._active_llm_instances[session_id]:
            # Логика выбора провайдера
            routing_config = self._load_routing_config()
            role_cfg = routing_config.get('roles', {}).get(role, {})
            provider_chain = role_cfg.get('providers', [])

            if not provider_chain:
                raise ValueError(f"No provider chain found for role: {role}")

            # Для простоты пока берем первого провайдера из цепочки
            # В будущем можно добавить логику выбора лучшего провайдера
            provider_name = provider_chain[0] 
            
            provider_adapters = self._get_provider_adapters()
            adapter_class = provider_adapters.get(provider_name)
            if not adapter_class:
                raise ValueError(f"Provider adapter not found for: {provider_name}")
            
            adapter = adapter_class(provider_name)
            self._active_llm_instances[session_id][role] = adapter
            logger.info(f"Created new LLM adapter for session {session_id}, role {role}, provider {provider_name}")
        
        return self._active_llm_instances[session_id][role]
    
    def _load_routing_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию роутинга из файла."""
        try:
            with open(ROUTING_CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            logger.error("routing_config_load_failed", error=str(e))
            raise
    
    def _get_provider_adapters(self):
        """Возвращает словарь адаптеров провайдеров."""
        # Импортируем провайдеры динамически, чтобы избежать циклического импорта
        from app.llm.providers.qwen import QwenAdapter
        from app.llm.providers.gemini import GeminiAdapter
        from app.llm.providers.claude import ClaudeAdapter
        from app.llm.providers.chat import ChatAdapter
        from app.llm.providers.gpt import GPTAdapter
        from app.llm.providers.stub import StubAdapter
        from app.llm.providers.codex import CodexAdapter
        
        return {
            # Qwen
            "qwen": QwenAdapter,
            "qwen_code": QwenAdapter,
            # Gemini
            "gemini": GeminiAdapter,
            "gemini_25_pro": GeminiAdapter,
            "gemini_25_flash": GeminiAdapter,
            # Claude / Anthropic
            "claude": ClaudeAdapter,
            "claude_opus_41": ClaudeAdapter,
            "anthropic_opus41": ChatAdapter,  # Для WebSocket чата используем ChatAdapter
            "claude_chat": ChatAdapter,
            # OpenAI via Codex
            "gpt": GPTAdapter,
            "gpt5": GPTAdapter,
            "openai_gpt5_via_codex": CodexAdapter,
            # Stub
            "stub": StubAdapter,
        }
    
    def _create_new_adapter(self, role: str) -> Any:
        """Создает новый временный адаптер без привязки к сессии."""
        routing_config = self._load_routing_config()
        role_cfg = routing_config.get('roles', {}).get(role, {})
        provider_chain = role_cfg.get('providers', [])

        if not provider_chain:
            raise ValueError(f"No provider chain found for role: {role}")

        provider_name = provider_chain[0] 
        
        provider_adapters = self._get_provider_adapters()
        adapter_class = provider_adapters.get(provider_name)
        if not adapter_class:
            raise ValueError(f"Provider adapter not found for: {provider_name}")
        
        adapter = adapter_class(provider_name)
        logger.info(f"Created temporary LLM adapter for role {role}, provider {provider_name}")
        return adapter

    def release_llm_adapter(self, session_id: str, role: str = None):
        """
        Освобождает LLM-адаптер для данной сессии и роли.
        Если role не указан, освобождает все адаптеры для сессии.
        """
        if session_id in self._active_llm_instances:
            if role and role in self._active_llm_instances[session_id]:
                del self._active_llm_instances[session_id][role]
                logger.info(f"Released LLM adapter for session {session_id}, role {role}")
            elif not role:
                del self._active_llm_instances[session_id]
                logger.info(f"Released all LLM adapters for session {session_id}")

    def get_active_sessions(self):
        return list(self._active_llm_instances.keys())
