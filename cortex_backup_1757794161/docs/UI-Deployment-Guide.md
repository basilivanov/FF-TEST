# UI Deployment Guide

## Обзор

Этот документ описывает процесс развертывания пользовательского интерфейса Feature Factory Admin UI.

## Сборка проекта

### Предварительные требования

- Node.js >= 16.0.0
- npm >= 8.0.0

### Установка зависимостей

```bash
cd /opt/feature-factory/app/ui
npm install
```

### Сборка для продакшена

```bash
cd /opt/feature-factory/app/ui
npm run build
```

Эта команда создаст оптимизированную сборку в директории `dist/`.

## Конфигурация

### Переменные окружения

UI использует следующие переменные окружения:

- `VITE_API_BASE_URL` - базовый URL для API (по умолчанию `/api/v1`)

Переменные окружения должны быть установлены в файле `.env.production` в директории `app/ui/`.

Пример `.env.production`:

```
VITE_API_BASE_URL=/api/v1
```

## Развертывание

### Nginx конфигурация

UI развертывается как статический сайт через Nginx. Конфигурация Nginx уже создана в файлах:

- `/opt/feature-factory/configs/nginx/etl-tst.chococraft.ru` (тестовое окружение)
- `/opt/feature-factory/configs/nginx/etl.chococraft.ru` (продакшен окружение)

Основные параметры конфигурации:

```nginx
location / {
    root /opt/feature-factory/app/ui/dist;
    try_files $uri $uri/ /index.html;
}

location /api/ {
    proxy_pass http://localhost:8080; # Для теста 8081
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Кэширование

Для оптимизации производительности настроено кэширование:

- `assets/*` - immutable кэширование на 365 дней
- `index.html` - no-store (всегда запрашивать свежую версию)

### Basic Auth

Доступ к UI защищен Basic Auth. Учетные данные хранятся в файле `.htpasswd` в директории Nginx.

## Деплой скрипт

Для автоматизации процесса деплоя создан скрипт `deploy_ui.sh`:

```bash
#!/bin/bash

# Перейти в директорию UI
cd /opt/feature-factory/app/ui

# Установить зависимости
npm install

# Собрать проект
npm run build

# Перезапустить Nginx
sudo systemctl reload nginx
```

Скрипт автоматически:
1. Определяет окружение (тест/продакшен)
2. Проверяет наличие необходимых файлов
3. Устанавливает зависимости
4. Собирает проект
5. Копирует файлы в директорию Nginx
6. Настраивает права доступа
7. Настраивает Nginx
8. Перезапускает Nginx
9. Проверяет доступность сайта

Для запуска скрипта:

```bash
sudo /opt/feature-factory/scripts/deploy_ui.sh
```

## Проверка развертывания

После развертывания проверьте:

1. Доступность сайта:
   ```bash
   curl -I https://etl-tst.chococraft.ru
   ```

2. Загрузку статических файлов:
   ```bash
   curl -I https://etl-tst.chococraft.ru/assets/index.js
   ```

3. Доступ к API:
   ```bash
   curl -I https://etl-tst.chococraft.ru/api/v1/health
   ```

## Откат изменений

Для отката изменений:

1. Восстановите предыдущую версию файлов из бэкапа
2. Пересоберите проект:
   ```bash
   cd /opt/feature-factory/app/ui
   npm run build
   ```
3. Перезапустите Nginx:
   ```bash
   sudo systemctl reload nginx
   ```

## Мониторинг

После развертывания убедитесь, что:

1. Сайт открывается без ошибок
2. Все API эндпоинты доступны
3. Нет ошибок в консоли браузера
4. Нет ошибок в логах Nginx:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

## Troubleshooting

### Проблемы с загрузкой страниц

- Проверьте конфигурацию Nginx
- Убедитесь, что файлы собранного проекта находятся в правильной директории
- Проверьте права доступа к файлам

### Проблемы с API

- Проверьте, запущен ли бэкенд сервис
- Проверьте конфигурацию прокси в Nginx
- Проверьте логи бэкенд сервиса

### Проблемы с авторизацией

- Проверьте файл `.htpasswd`
- Проверьте конфигурацию Basic Auth в Nginx
- Убедитесь, что учетные данные верны

## Best Practices

1. **Всегда тестируйте изменения в тестовом окружении перед продакшеном**
2. **Делайте бэкапы перед каждым деплоем**
3. **Мониторьте логи после деплоя**
4. **Используйте версионирование для отслеживания изменений**
5. **Автоматизируйте процесс деплоя через CI/CD**