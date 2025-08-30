#!/usr/bin/env python3
"""
Модуль роутера LLM с поддержкой CLI-транспорта и роутинга по ролям.
"""

import time
import yaml
import hashlib
from typing import List, Dict, Any, Tuple
import structlog

from app.llm.session_manager import LLMSessionManager # Новый импорт

from app.llm.transports.cli import run_cli, CliExecError, CliTimeoutError
from app.llm.providers.qwen import QwenAdapter
from app.llm.providers.gemini import GeminiAdapter
from app.llm.providers.claude import ClaudeAdapter
from app.llm.providers.chat import ChatAdapter
from app.llm.providers.gemini_chat import GeminiChatAdapter
from app.llm.providers.gpt import GPTAdapter
from app.llm.providers.stub import StubAdapter
from app.llm.providers.codex import CodexAdapter
from app.llm.token_budget import check_role_budget, BudgetExceeded
from app.llm.token_accountant import get_token_accountant

# Настройка логгера
logger = structlog.get_logger()

# Получаем экземпляр счетчика токенов
token_accountant = get_token_accountant()

# Создаем экземпляр LLMSessionManager
llm_session_manager = LLMSessionManager()

# Путь к конфигурационному файлу роутинга
ROUTING_CONFIG_PATH = "/opt/feature-factory/configs/llm_routing.yaml"
CLI_DECL_CONFIG_PATH = "/opt/feature-factory/configs/llm_cli_config.yaml"
FF_UNIVERSAL_WRAPPER = "/opt/feature-factory/bin/ff-cli-wrapper.sh"

# Словарь доступных провайдеров
PROVIDER_ADAPTERS = {
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
    "anthropic_opus41": ClaudeAdapter,
    # OpenAI via Codex
    "gpt": GPTAdapter,
    "gpt5": GPTAdapter,
    "openai_gpt5_via_codex": CodexAdapter,
    # Stub
    "stub": StubAdapter,
}

class RETRYABLE_ERROR(Exception):
    """Исключение для ошибок, которые можно повторить."""
    pass

# --- Declarative CLI config support (Nexus) ---
import os, json, uuid, re
from app.utils.secret_store import decrypt_value
try:
    from app.db.session import SessionLocal
except Exception:
    SessionLocal = None

_DECL_CFG = None

def _load_cli_decl_config() -> Dict[str, Any] | None:
    global _DECL_CFG
    if _DECL_CFG is not None:
        return _DECL_CFG
    if not os.path.exists(CLI_DECL_CONFIG_PATH):
        _DECL_CFG = None
        return None
    with open(CLI_DECL_CONFIG_PATH, 'r') as f:
        _DECL_CFG = yaml.safe_load(f)
        return _DECL_CFG

def _resolve_secret_refs(val: Any) -> Any:
    """Рекурсивно заменяет вхождения вида <SECRET:KEY> на реальные значения из секрет-стора."""
    pattern = re.compile(r"<SECRET:([A-Za-z0-9_\-\.]+)>")

    def _fetch_secret(key: str) -> str:
        if SessionLocal is None:
            return ""
        db = SessionLocal()
        try:
            row = db.execute(
                "SELECT value_enc FROM secrets WHERE key = :k",
                {"k": key},
            ).fetchone()
            if not row:
                return ""
            return decrypt_value(row[0])
        except Exception:
            return ""
        finally:
            db.close()

    def _subst(s: str) -> str:
        def repl(m):
            k = m.group(1)
            return _fetch_secret(k) or ""
        return pattern.sub(repl, s)

    if isinstance(val, dict):
        return {k: _resolve_secret_refs(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_resolve_secret_refs(x) for x in val]
    if isinstance(val, str):
        return _subst(val)
    return val

def _format_messages_for_prompt(messages: List[Dict[str, str]]) -> str:
    parts = []
    for m in messages:
        role = m.get('role', 'user')
        content = m.get('content', '')
        parts.append(f"{role}: {content}")
    return "\n".join(parts)

def _alias_to_decl(provider_name: str, mode: str | None, decl_cfg: Dict[str, Any]) -> Tuple[str, str | None]:
    aliases = decl_cfg.get('aliases', {})
    a = aliases.get(provider_name)
    if a and isinstance(a, dict):
        return a.get('provider', provider_name), a.get('model')
    return provider_name, None

def _build_decl_cli(provider_name: str, role_cfg: Dict[str, Any], mode: str | None,
                    messages: List[Dict[str, str]]) -> Tuple[List[str], Dict[str, str], str | None, Dict[str, Any], str]:
    """
    Возвращает (cmd, env, input_data, prov_cfg, model_id) на основе декларативного YAML.
    """
    decl = _load_cli_decl_config()
    if not decl:
        raise ValueError("Declarative CLI config not found")

    base_provider, alias_model = _alias_to_decl(provider_name, mode, decl)
    prov = decl.get('providers', {}).get(base_provider)
    if not prov:
        raise ValueError(f"Provider '{provider_name}' not found in declarative config")

    # stdin mode
    stdin_mode = prov.get('stdin', 'messages_json')

    # model selection
    model_key = alias_model
    if not model_key and mode:
        model_key = (prov.get('modes', {}).get(mode, {}) or {}).get('model')
    if not model_key:
        model_key = 'default'
    model_entry = (prov.get('models', {}) or {}).get(model_key) or prov.get('models', {}).get('default') or {}
    model_id = model_entry.get('id', 'unknown')

    # command assembly
    # Универсальная обёртка + реальный бинарь из конфигурации
    binary_path = prov.get('binary_path')
    if not binary_path:
        raise ValueError(f"binary_path is missing for provider {base_provider}")
    cmd: List[str] = [FF_UNIVERSAL_WRAPPER, binary_path]
    flags = list(prov.get('flags', {}).get('base', []) or [])
    # per-model flags
    flags += list(model_entry.get('flags', []) or [])
    # generic model flag support
    model_flag = prov.get('flags', {}).get('model_flag')
    if model_flag and model_flag not in flags:
        flags += [model_flag, model_id]

    # handle outfile placeholder for codex
    outfile = None
    if prov.get('output_parser') == 'textfile':
        tmpl = prov.get('outfile_template', '/tmp/ff_out_${UUID}.txt')
        outfile = tmpl.replace('${UUID}', uuid.uuid4().hex)
        flags = [outfile if x == '${OUTFILE}' else x for x in flags]

    cmd += flags

    # env with secrets
    env_cfg = _resolve_secret_refs(prov.get('env', {}) or {})
    # drop empty values
    env = {k: v for k, v in env_cfg.items() if v}

    # input
    input_data = None
    if stdin_mode == 'messages_json':
        input_data = json.dumps({"messages": messages}, ensure_ascii=False)
    elif stdin_mode == 'prompt':
        input_data = None
        # prompt will be passed via flags; append -p if not already present
        prompt = _format_messages_for_prompt(messages)
        # try known pattern: -p <text>
        if '-p' not in cmd:
            cmd += ['-p', prompt]
        else:
            # replace the last '-p' value if placeholder present
            try:
                idx = cmd.index('-p')
                if idx == len(cmd) - 1:
                    cmd.append(prompt)
                else:
                    cmd[idx + 1] = prompt
            except Exception:
                cmd += ['-p', prompt]
    else:
        input_data = None

    # attach outfile path as part of prov cfg for parser
    if outfile:
        prov = dict(prov)
        prov['__outfile'] = outfile

    return cmd, env, input_data, prov, model_id

_ACCESS_TOKEN_CACHE: Dict[str, Dict[str, Any]] = {}

def _inject_oauth_access_token(provider_name: str, prov_cfg: Dict[str, Any], cmd: List[str], env: Dict[str, str]) -> None:
    """Получает access_token по refresh_token и внедряет его в команду/окружение согласно конфигу.
    Включает TTL-кэш (10 мин) и синхронизацию локальных конфигов CLI.
    """
    decl = _load_cli_decl_config() or {}
    base_provider, _ = _alias_to_decl(provider_name, None, decl)
    prov = decl.get('providers', {}).get(base_provider) or {}
    auth_cfg = _resolve_secret_refs(prov.get('auth', {}) or {})
    refresh_key = auth_cfg.get('refresh_secret_key')
    if not refresh_key:
        return
    # достаём refresh_token из секретов
    refresh_token = None
    if SessionLocal is not None:
        db = SessionLocal()
        try:
            row = db.execute("SELECT value_enc FROM secrets WHERE key = :k", {"k": refresh_key}).fetchone()
            if row:
                refresh_token = decrypt_value(row[0])
        except Exception:
            refresh_token = None
        finally:
            db.close()
    if not refresh_token:
        return
    # Собираем auth_config и проверяем кэш
    auth_cfg["refresh_token"] = refresh_token
    now = time.time()
    cached = _ACCESS_TOKEN_CACHE.get(provider_name)
    if cached and (now - cached.get("ts", 0) < 600) and cached.get("token"):
        access_token = cached["token"]
    else:
        adapter_class = PROVIDER_ADAPTERS.get(provider_name)
        if not adapter_class:
            return
        adapter = adapter_class(provider_name)
        access_token = None
        try:
            if hasattr(adapter, 'get_fresh_access_token'):
                access_token = adapter.get_fresh_access_token(auth_cfg)
        except Exception:
            access_token = None
        if not access_token:
            return
        # Синхронизируем локальные конфиги CLI
        try:
            if hasattr(adapter, 'update_local_config_file'):
                adapter.update_local_config_file(access_token, auth_cfg)
        except Exception:
            pass
        _ACCESS_TOKEN_CACHE[provider_name] = {"token": access_token, "ts": now}
    # внедрение в команду
    access_flag = auth_cfg.get('access_token_flag')
    access_env = auth_cfg.get('access_env')
    if access_env:
        env[access_env] = access_token
    if access_flag:
        cmd.extend([access_flag, access_token])

def _load_routing_config() -> Dict[str, Any]:
    """Загружает конфигурацию роутинга из файла."""
    try:
        with open(ROUTING_CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
            print(f"DEBUG: Loaded routing config: {config}") # DEBUG
            return config
    except Exception as e:
        logger.error("routing_config_load_failed", error=str(e))
        raise

def _get_prompt_hash(messages: List[Dict[str, str]]) -> str:
    """Вычисляет хэш от prompt для логирования."""
    prompt_text = "".join([msg.get("content", "") for msg in messages])
    return hashlib.md5(prompt_text.encode()).hexdigest()

def _filter_providers_by_mode(provider_chain: List[str], role_cfg: Dict[str, Any], mode: str) -> List[str]:
    """
    Фильтрует список провайдеров в зависимости от режима.
    
    Args:
        provider_chain: Список провайдеров из конфигурации.
        role_cfg: Конфигурация роли.
        mode: Режим работы ('reasoning' или 'fast').
        
    Returns:
        Отфильтрованный список провайдеров.
    """
    if mode not in ['reasoning', 'fast']:
        # Если режим не указан или не поддерживается, возвращаем все провайдеры
        return provider_chain
    
    filtered_providers = []
    
    # Получаем параметры роли
    reasoning_effort = role_cfg.get('reasoning_effort', 'minimal')
    extended_thinking = role_cfg.get('extended_thinking', False)
    adaptive_thinking = role_cfg.get('adaptive_thinking', False)
    
    for provider in provider_chain:
        # Особое ограничение: Qwen может использоваться только в режиме 'fast'
        if mode == 'reasoning' and provider.startswith('qwen'):
            # Пропускаем Qwen в режиме reasoning
            continue
            
        if mode == 'reasoning':
            # В режиме reasoning выбираем провайдеров, если роль поддерживает высокий уровень рассуждений
            if reasoning_effort == 'high' or extended_thinking or adaptive_thinking:
                filtered_providers.append(provider)
        elif mode == 'fast':
            # В режиме fast выбираем провайдеров, если роль поддерживает минимальный уровень рассуждений
            if reasoning_effort == 'minimal':
                filtered_providers.append(provider)
                
    # Если не нашли провайдеров по критериям режима, возвращаем пустой список
    # Это будет обработано вызывающим кодом
    return filtered_providers

def completion(role: str, messages: List[Dict[str, str]], max_tokens: int,
               temperature: float, stop: List[str] = None, timeout_s: int = None,
               return_trace: bool = False, mode: str = None, session_id: str = None) -> Dict[str, Any]:
    """
    Выполняет завершение (completion) с использованием LLM через CLI с роутингом по ролям.
    
    Args:
        role: Роль агента (Dev, QA, Scribe, Architect, Maintainer).
        messages: Список сообщений в формате OpenAI.
        max_tokens: Максимальное количество токенов в ответе.
        temperature: Температура генерации.
        stop: Список стоп-слов.
        timeout_s: Таймаут выполнения в секундах (если None, берется из конфигурации).
        mode: Режим работы ('reasoning' или 'fast'). Если None, используются все провайдеры.
        
    Returns:
        Dict[str, Any]: Унифицированный контракт ответа.
        
    Raises:
        BudgetExceeded: Если бюджет токенов для роли превышен.
        RETRYABLE_ERROR: Для ошибок, которые можно повторить.
        Exception: Для других ошибок.
    """
    # Загружаем конфигурацию роутинга
    routing_config = _load_routing_config()
    
    # Получаем конфиг роли и цепочку провайдеров
    role_cfg = routing_config.get('roles', {}).get(role, {})
    provider_chain = role_cfg.get('providers', [])
    if not provider_chain:
        raise ValueError(f"No provider chain found for role: {role}")
    
    # Фильтруем провайдеры по режиму, если режим задан
    if mode:
        provider_chain = _filter_providers_by_mode(provider_chain, role_cfg, mode)
        if not provider_chain:
            logger.warning(
                "llm_call_no_providers_after_mode_filtering",
                component="llm",
                role=role,
                mode=mode
            )
            # Если после фильтрации не осталось провайдеров, возвращаем ошибку
            raise ValueError(f"No providers available for role {role} in mode {mode}")
    
    # Получаем таймаут для роли, если не задан явно
    if timeout_s is None:
        # Пытаемся взять таймаут из конфигурации роли (timeout_sec), иначе 60
        timeout_s = int(role_cfg.get('timeout_sec', 60))
    
    # Вычисляем хэш prompt'а для логирования
    prompt_hash = _get_prompt_hash(messages)
    
    # Оцениваем количество токенов перед вызовом
    # Это нужно для проверки бюджета
    if provider_chain:
        # Берем первого провайдера для оценки
        first_provider = provider_chain[0]
        # Для модели возьмем что-то подходящее для первого провайдера
        model_map = {
            "qwen": "qwen3-coder:14b",
            "qwen_code": "qwen3-coder:14b",
            "gemini": "gemini-pro",
            "gemini_25_pro": "gemini-2.5-pro",
            "gemini_25_flash": "gemini-2.5-flash",
            "claude": "claude-3-5-sonnet",
            "claude_opus_41": "claude-4.1-opus",
            "anthropic_opus41": "claude-4.1-opus",
            "gpt": "gpt-4o-mini",
            "gpt5": "gpt-5",
            "openai_gpt5_via_codex": "gpt-5",
            "stub": "stub-1.0"
        }
        model = model_map.get(first_provider, "unknown")
        
        # Оцениваем количество токенов
        estimated_input_tokens, estimated_output_tokens = token_accountant.estimate_tokens(
            first_provider, model, messages
        )
        
        # Проверяем бюджет роли перед вызовом
        try:
            check_role_budget(role, estimated_input_tokens)
        except BudgetExceeded as e:
            logger.info(
                "llm_call_budget_exceeded",
                component="llm",
                role=role,
                estimated_input_tokens=estimated_input_tokens,
                estimated_output_tokens=estimated_output_tokens
            )
            raise
    
    # Получаем fallback конфигурацию  
    fallback_config = routing_config.get("fallback", {})
    # YAML 1.1 может интерпретировать ключ 'on' как boolean True.
    # Поддержим оба варианта для устойчивости конфигурации.
    fallback_conditions = fallback_config.get("on") or fallback_config.get(True) or ["RC_NONZERO"]
    
    # Попробуем каждый провайдер из цепочки с fallback логикой
    start_time = time.time()
    last_exception = None
    
    for provider_idx, provider_name in enumerate(provider_chain):
        try:
            logger.info(f"[FALLBACK] Trying provider {provider_idx+1}/{len(provider_chain)}: {provider_name}")
            
            # Вариант 1: Декларативная сборка (если конфиг присутствует)
            decl_cfg = _load_cli_decl_config()
            use_decl = False
            if decl_cfg:
                # проверим, что можем сопоставить провайдера
                base_provider, _ = _alias_to_decl(provider_name, mode, decl_cfg)
                if base_provider in (decl_cfg.get('providers') or {}):
                    use_decl = True

            # Логируем вызов провайдера
            logger.info(
                "llm_call_attempt",
                component="llm",
                role=role,
                provider=provider_name,
                attempt=provider_idx+1,
                prompt_hash=prompt_hash,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout_s
            )
            
            # Настраиваем таймаут для провайдера
            provider_timeout = timeout_s
            if provider_name == "openai_gpt5_via_codex":
                provider_timeout = max(timeout_s or 0, 55)

            # Выполняем через декларативную сборку или через адаптер как раньше
            if use_decl:
                cmd, env, input_data, prov_cfg, model_id = _build_decl_cli(provider_name, role_cfg, mode, messages)
                # Внедряем access_token при наличии refresh_token
                try:
                    _inject_oauth_access_token(provider_name, prov_cfg, cmd, env)
                except Exception:
                    pass
                logger.info(f"[BASE DEBUG] Provider: {provider_name}, cmd: {' '.join(cmd)}")
                rc, stdout, stderr = run_cli(cmd, env, timeout_s=provider_timeout, input_data=input_data)
                logger.info(f"[BASE DEBUG] return_code: {rc}, stderr: {stderr}")
                if rc != 0:
                    raise Exception(f"CLI command failed with code {rc}: {stderr}")

                parser = prov_cfg.get('output_parser', 'json')
                if parser == 'text':
                    result = {
                        "provider": provider_name,
                        "model": model_id,
                        "text": stdout.strip(),
                        "usage": {"input_tokens": 0, "output_tokens": max(10, len(stdout)//4), "estimated": True},
                        "finish_reason": "stop",
                        "choices": [{"message": {"content": stdout.strip()}}],
                    }
                elif parser == 'textfile':
                    of = prov_cfg.get('__outfile')
                    content = ""
                    if of and os.path.exists(of):
                        try:
                            with open(of, 'r', encoding='utf-8') as f:
                                content = f.read().strip()
                        finally:
                            try:
                                os.remove(of)
                            except Exception:
                                pass
                    result = {
                        "provider": provider_name,
                        "model": model_id,
                        "text": content,
                        "usage": {"input_tokens": 0, "output_tokens": max(10, len(content)//4), "estimated": True},
                        "finish_reason": "stop",
                        "choices": [{"message": {"content": content}}],
                    }
                else:
                    # попытка распарсить JSON напрямую
                    try:
                        parsed = json.loads(stdout)
                    except Exception as je:
                        raise Exception(f"JSON parse failed: {je}")
                    result = parsed
            else:
                adapter_class = PROVIDER_ADAPTERS.get(provider_name)
                if not adapter_class:
                    logger.warning(f"Provider adapter not found: {provider_name}")
                    continue
                adapter = adapter_class(provider_name)
                result = adapter.complete(messages, max_tokens, temperature, stop, timeout_s=provider_timeout)
            logger.info(f"[FALLBACK] Provider {provider_name} succeeded")
            
            # Успех! Выходим из цикла
            break
            
        except Exception as e:
            last_exception = e
            error_type = type(e).__name__
            logger.warning(
                "llm_provider_failed", 
                provider=provider_name,
                error=str(e)[:200],
                error_type=error_type,
                attempt=provider_idx+1
            )
            
            # Проверяем подходит ли ошибка для fallback
            err_text = str(e)
            err_lower = err_text.lower()
            should_fallback = (
                ("RC_NONZERO" in fallback_conditions and "CLI command failed" in err_text)
                or ("TIMEOUT" in fallback_conditions and ("timeout" in err_lower or "timed out" in err_lower))
                or ("JSON_PARSE_ERROR" in fallback_conditions and "json" in err_lower)
            )
            
            if not should_fallback or provider_idx == len(provider_chain) - 1:
                # Последний провайдер или ошибка не подходит для fallback
                logger.error(f"[FALLBACK] All providers failed, last error: {e}")
                raise e
                
            logger.info(f"[FALLBACK] Falling back to next provider...")
            continue
    else:
        # Этот блок выполнится если цикл завершился без break (все провайдеры упали)
        raise Exception(f"All providers failed for role {role}. Last error: {last_exception}")
        
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Получаем информацию об использовании токенов из результата
    usage = result.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    estimated = usage.get("estimated", False)
    
    # Если в результате нет информации об использовании токенов, 
    # оцениваем ее
    if input_tokens == 0 and output_tokens == 0:
        # Для модели возьмем что-то подходящее
        model_map = {
                "qwen": "qwen3-coder:14b",
                "qwen_code": "qwen3-coder:14b",
                "gemini": "gemini-pro",
                "gemini_25_pro": "gemini-2.5-pro",
                "gemini_25_flash": "gemini-2.5-flash",
                "claude": "claude-3-5-sonnet",
                "claude_opus_41": "claude-4.1-opus",
                "anthropic_opus41": "claude-4.1-opus",
                "gpt": "gpt-4o-mini",
                "gpt5": "gpt-5",
                "openai_gpt5_via_codex": "gpt-5",
                "stub": "stub-1.0"
        }
        model = model_map.get(provider_name, "unknown")
        
        # Оцениваем количество токенов
        input_tokens, output_tokens = token_accountant.estimate_tokens(
            provider_name, model, messages
        )
        estimated = True
    
    # Записываем использование токенов
    token_accountant.record_usage(
        role, 
        provider_name, 
        result.get("model", "unknown"), 
        input_tokens, 
        output_tokens, 
        estimated
    )
    
    # Логируем успешный вызов
    logger.info(
        "llm_call_end",
        component="llm",
        role=role,
        provider=provider_name,
        model=result.get("model", "unknown"),
        prompt_hash=prompt_hash,
        usage={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated": estimated
        },
        latency_ms=latency_ms,
        finish_reason=result.get("finish_reason", "stop"),
        mode=mode
    )
    
    # Нормализуем в OpenAI-стиль для потребителей, ожидающих choices[0].message.content
    if isinstance(result, dict) and "choices" not in result:
        text = result.get("text", "")
        result = {
            **result,
            "choices": [{"message": {"content": text}}],
        }

    if return_trace:
        result = dict(result)
        result["trace"] = trace
    
    return result
