# Backup and Recovery Guide

## Обзор

Этот документ описывает процедуры резервного копирования и восстановления данных Feature Factory.

## Бэкап данных

### Базы данных

Базы данных SQLite бэкапятся ежедневно:
- Тест: `/opt/feature-factory/data/test.db`
- Продакшен: `/opt/feature-factory/data/prod.db`

### Индексные файлы

Индексные файлы бэкапятся ежедневно:
- `/opt/feature-factory/data/code_registry.jsonl`
- `/opt/feature-factory/data/symbol_index.jsonl`
- `/opt/feature-factory/data/call_graph.dot`

### Конфигурационные файлы

Конфигурационные файлы бэкапятся ежедневно:
- `/opt/feature-factory/configs/`
- `/opt/feature-factory/.env`

### Логи

Логи бэкапятся ежедневно:
- `/opt/feature-factory/logs/`

## Процедура бэкапа

### Автоматический бэкап

Автоматический бэкап выполняется скриптом `scripts/backup.sh` по расписанию через cron.

#### Скрипт бэкапа

```bash
#!/bin/bash

# Скрипт для бэкапа данных Feature Factory

set -e

# Переменные
BACKUP_DIR="/opt/feature-factory/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="feature-factory-backup-$DATE"

# Создание директории бэкапа
mkdir -p $BACKUP_DIR/$BACKUP_NAME

# Бэкап баз данных
cp /opt/feature-factory/data/test.db $BACKUP_DIR/$BACKUP_NAME/
cp /opt/feature-factory/data/prod.db $BACKUP_DIR/$BACKUP_NAME/

# Бэкап индексных файлов
cp /opt/feature-factory/data/code_registry.jsonl $BACKUP_DIR/$BACKUP_NAME/
cp /opt/feature-factory/data/symbol_index.jsonl $BACKUP_DIR/$BACKUP_NAME/
cp /opt/feature-factory/data/call_graph.dot $BACKUP_DIR/$BACKUP_NAME/

# Бэкап конфигурационных файлов
cp -r /opt/feature-factory/configs/ $BACKUP_DIR/$BACKUP_NAME/

# Бэкап .env файла
cp /opt/feature-factory/.env $BACKUP_DIR/$BACKUP_NAME/

# Бэкап логов
cp -r /opt/feature-factory/logs/ $BACKUP_DIR/$BACKUP_NAME/

# Архивация
tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz -C $BACKUP_DIR $BACKUP_NAME

# Удаление временной директории
rm -rf $BACKUP_DIR/$BACKUP_NAME

# Удаление старых бэкапов (оставляем последние 30)
ls -t $BACKUP_DIR/*.tar.gz | tail -n +31 | xargs -r rm

echo "Backup completed: $BACKUP_DIR/$BACKUP_NAME.tar.gz"
```

#### Расписание cron

Бэкап выполняется ежедневно в 2:00:

```cron
0 2 * * * /opt/feature-factory/scripts/backup.sh
```

### Ручной бэкап

Ручной бэкап можно выполнить командой:

```bash
sudo /opt/feature-factory/scripts/backup.sh
```

## Хранение бэкапов

### Локальное хранение

Бэкапы хранятся в директории `/opt/feature-factory/backups/`.

### Удаленное хранение

Бэкапы копируются на удаленный сервер через rsync:

```bash
rsync -avz --delete /opt/feature-factory/backups/ user@backup-server:/backups/feature-factory/
```

### Политика хранения

- Локально: последние 30 бэкапов
- Удаленно: последние 90 бэкапов

## Восстановление данных

### Процедура восстановления

#### 1. Остановка сервисов

```bash
sudo systemctl stop feature-factory-test
sudo systemctl stop feature-factory-prod
sudo systemctl stop nginx
```

#### 2. Восстановление базы данных

```bash
# Распаковка бэкапа
tar -xzf /opt/feature-factory/backups/feature-factory-backup-YYYYMMDD_HHMMSS.tar.gz -C /tmp/

# Восстановление тестовой базы
cp /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/test.db /opt/feature-factory/data/test.db

# Восстановление продакшен базы
cp /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/prod.db /opt/feature-factory/data/prod.db

# Установка прав доступа
chown feature-factory:feature-factory /opt/feature-factory/data/test.db
chown feature-factory:feature-factory /opt/feature-factory/data/prod.db
chmod 600 /opt/feature-factory/data/test.db
chmod 600 /opt/feature-factory/data/prod.db
```

#### 3. Восстановление индексных файлов

```bash
# Восстановление индексных файлов
cp /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/code_registry.jsonl /opt/feature-factory/data/
cp /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/symbol_index.jsonl /opt/feature-factory/data/
cp /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/call_graph.dot /opt/feature-factory/data/

# Установка прав доступа
chown feature-factory:feature-factory /opt/feature-factory/data/code_registry.jsonl
chown feature-factory:feature-factory /opt/feature-factory/data/symbol_index.jsonl
chown feature-factory:feature-factory /opt/feature-factory/data/call_graph.dot
chmod 600 /opt/feature-factory/data/code_registry.jsonl
chmod 600 /opt/feature-factory/data/symbol_index.jsonl
chmod 600 /opt/feature-factory/data/call_graph.dot
```

#### 4. Восстановление конфигурационных файлов

```bash
# Восстановление конфигурационных файлов
cp -r /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/configs/ /opt/feature-factory/

# Установка прав доступа
chown -R feature-factory:feature-factory /opt/feature-factory/configs/
chmod -R 600 /opt/feature-factory/configs/
```

#### 5. Восстановление .env файла

```bash
# Восстановление .env файла
cp /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/.env /opt/feature-factory/

# Установка прав доступа
chown feature-factory:feature-factory /opt/feature-factory/.env
chmod 600 /opt/feature-factory/.env
```

#### 6. Восстановление логов

```bash
# Восстановление логов (опционально)
cp -r /tmp/feature-factory-backup-YYYYMMDD_HHMMSS/logs/ /opt/feature-factory/
```

#### 7. Запуск сервисов

```bash
sudo systemctl start nginx
sudo systemctl start feature-factory-test
sudo systemctl start feature-factory-prod
```

### Проверка восстановления

После восстановления необходимо проверить:
- Доступность API
- Доступность UI
- Целостность данных
- Работу индекса

## Point-in-Time Recovery

### WAL журналы

SQLite поддерживает WAL (Write-Ahead Logging) режим, который позволяет восстановление на определенный момент времени.

#### Включение WAL режима

```sql
PRAGMA journal_mode=WAL;
```

#### Бэкап WAL журналов

WAL журналы бэкапятся вместе с базой данных.

#### Восстановление на определенный момент времени

Для восстановления на определенный момент времени:
1. Восстановить базу данных из бэкапа
2. Применить WAL журналы до нужного момента

## Тестирование восстановления

### Регулярное тестирование

Регулярно тестируется процедура восстановления:
- Ежемесячно на тестовом окружении
- При изменении процедуры бэкапа

### План тестирования

1. Создать тестовое окружение
2. Выполнить восстановление из бэкапа
3. Проверить целостность данных
4. Проверить работоспособность сервисов
5. Задокументировать результаты

## Мониторинг бэкапов

### Проверка успешности бэкапа

После каждого бэкапа проверяется:
- Успешное завершение скрипта
- Наличие файла бэкапа
- Целостность файла бэкапа

### Алерты

Настроены алерты:
- При неуспешном бэкапе
- При отсутствии бэкапа более 24 часов
- При низком свободном месте на диске

## Disaster Recovery

### План восстановления после аварии

#### 1. Оценка ситуации

- Определить причину аварии
- Оценить масштаб повреждений
- Определить доступные бэкапы

#### 2. Восстановление инфраструктуры

- Восстановить сервер (при необходимости)
- Установить необходимое ПО
- Настроить окружение

#### 3. Восстановление данных

- Выполнить восстановление из бэкапа
- Проверить целостность данных
- Протестировать работу сервисов

#### 4. Восстановление сервисов

- Запустить сервисы
- Проверить доступность API и UI
- Проверить мониторинг

### Критерии восстановления

#### RTO (Recovery Time Objective)

Максимальное время восстановления: 4 часа

#### RPO (Recovery Point Objective)

Максимальная потеря данных: 24 часа

## Best Practices

### Бэкап

1. **Регулярно тестируйте бэкапы**
2. **Храните бэкапы в нескольких местах**
3. **Шифруйте чувствительные бэкапы**
4. **Мониторьте процесс бэкапа**
5. **Ограничьте доступ к бэкапам**

### Восстановление

1. **Документируйте процедуру восстановления**
2. **Регулярно тестируйте восстановление**
3. **Имейте план восстановления после аварии**
4. **Ограничьте доступ к восстановлению**
5. **Проверяйте целостность данных после восстановления**

## Полезные команды

### Проверка целостности базы данных

```bash
sqlite3 /opt/feature-factory/data/test.db "PRAGMA integrity_check;"
```

### Создание бэкапа базы данных

```bash
sqlite3 /opt/feature-factory/data/test.db ".backup /opt/feature-factory/backups/test.db.backup"
```

### Восстановление базы данных из бэкапа

```bash
mv /opt/feature-factory/data/test.db /opt/feature-factory/data/test.db.old
cp /opt/feature-factory/backups/test.db.backup /opt/feature-factory/data/test.db
```

### Проверка размера бэкапов

```bash
du -sh /opt/feature-factory/backups/*
```

### Очистка старых бэкапов

```bash
find /opt/feature-factory/backups/ -name "*.tar.gz" -mtime +30 -delete
```

## troubleshooting

### Проблемы с бэкапом

#### Бэкап не завершается

1. Проверьте логи скрипта бэкапа
2. Проверьте свободное место на диске
3. Проверьте права доступа к файлам

#### Бэкап поврежден

1. Проверьте контрольные суммы
2. Создайте новый бэкап
3. Исключите поврежденный бэкап из ротации

### Проблемы с восстановлением

#### Восстановление не удается

1. Проверьте целостность бэкапа
2. Проверьте права доступа к файлам
3. Проверьте зависимости ПО

#### Данные не восстанавливаются

1. Проверьте версию SQLite
2. Проверьте совместимость схемы базы данных
3. Проверьте целостность WAL журналов

## Контакты

По вопросам бэкапа и восстановления обращайтесь к команде DevOps по адресу devops@chococraft.ru.