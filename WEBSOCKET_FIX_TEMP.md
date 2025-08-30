# Временное исправление WebSocket чата

## Проблема
WebSocket чат возвращает `CLI command failed with return code 1` 

## Исправления применены
- ✅ ChatAdapter для текстового режима
- ✅ ChatMaintainer роль с stub провайдером  
- ✅ CLI конфигурация исправлена

## Статус
- ✅ HTTP чат работает: `/api/v1/chat/maintainer`
- ❌ WebSocket чат: старые модули в memory

## Для полного исправления
Требуется СИСТЕМНЫЙ перезапуск сервера для очистки Python memory cache:
```bash
sudo systemctl restart feature-factory-test
```

## Для пользователей
До перезапуска используйте HTTP чат вместо WebSocket - он полностью функционален.