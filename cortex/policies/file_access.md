# Политики доступа к файлам

## Разрешенные директории для агентов

### Полный доступ (чтение/запись)
- `/opt/feature-factory/artifacts/` — артефакты выполнения задач
- `/opt/feature-factory/data/` — данные приложения (БД, индексы)
- `/opt/feature-factory/tmp/` — временные файлы 
- `/opt/feature-factory/backups/` — бэкапы системы

### Только чтение
- `/opt/feature-factory/app/` — исходный код приложения
- `/opt/feature-factory/cortex/` — документация и правила
- `/opt/feature-factory/scripts/` — скрипты автоматизации
- `/opt/feature-factory/configs/` — конфигурационные файлы

### Ограниченный доступ
- `/home/feature/` — домашняя директория пользователя feature
- `/home/feature/.ssh/` — SSH ключи (только для Git операций)
- `/home/feature/.nvm/` — Node Version Manager

## Запрещенные операции

### Системные директории
- **ЗАПРЕЩЕНО:** запись в `/usr`, `/bin`, `/sbin`, `/lib`
- **ЗАПРЕЩЕНО:** чтение `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`
- **ЗАПРЕЩЕНО:** доступ к `/root/` и другим пользовательским `/home/*`

### Критические файлы
- **ЗАПРЕЩЕНО:** модификация systemd unit файлов без sudo
- **ЗАПРЕЩЕНО:** изменение nginx конфигурации напрямую
- **ЗАПРЕЩЕНО:** доступ к логам других пользователей в `/var/log`

### Временные ограничения
- Файлы в `/opt/feature-factory/tmp/` удаляются через 24 часа
- Артефакты старше 30 дней подлежат архивированию
- Бэкапы хранятся максимум 7 дней

## Permissions схема

### Директории
```bash
/opt/feature-factory/artifacts/  — 755 feature:feature
/opt/feature-factory/data/       — 700 feature:feature  
/opt/feature-factory/tmp/        — 755 feature:feature
/opt/feature-factory/backups/    — 700 feature:feature
```

### Файлы БД
```bash
*.db файлы                       — 600 feature:feature
*.db-wal, *.db-shm              — 600 feature:feature
```

### Executable файлы
```bash
/opt/feature-factory/bin/*      — 755 feature:feature
```