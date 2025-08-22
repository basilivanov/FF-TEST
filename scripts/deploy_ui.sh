#!/bin/bash

# Скрипт для деплоя UI Feature Factory

set -e  # Остановить выполнение при ошибках

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка прав администратора
check_sudo() {
    if [ "$EUID" -ne 0 ]; then
        log_error "Этот скрипт должен быть запущен с правами sudo"
        exit 1
    fi
}

# Определение окружения
detect_environment() {
    if [ -f "/etc/default/feature-factory-prod" ]; then
        ENV="prod"
        CONFIG_FILE="/etc/default/feature-factory-prod"
        NGINX_CONFIG="/opt/feature-factory/configs/nginx/etl.chococraft.ru"
        NGINX_HTACCESS="/opt/feature-factory/configs/nginx/.htpasswd"
        DOMAIN="etl.chococraft.ru"
    elif [ -f "/etc/default/feature-factory-test" ]; then
        ENV="test"
        CONFIG_FILE="/etc/default/feature-factory-test"
        NGINX_CONFIG="/opt/feature-factory/configs/nginx/etl-tst.chococraft.ru"
        NGINX_HTACCESS="/opt/feature-factory/configs/nginx/.htpasswd"
        DOMAIN="etl-tst.chococraft.ru"
    else
        log_error "Не удалось определить окружение. Убедитесь, что установлены файлы конфигурации."
        exit 1
    fi
    
    log "Обнаружено окружение: $ENV"
}

# Проверка наличия необходимых файлов
check_files() {
    if [ ! -d "/opt/feature-factory/app/ui" ]; then
        log_error "Директория UI не найдена: /opt/feature-factory/app/ui"
        exit 1
    fi
    
    if [ ! -f "$NGINX_CONFIG" ]; then
        log_error "Конфигурационный файл Nginx не найден: $NGINX_CONFIG"
        exit 1
    fi
    
    log "Все необходимые файлы присутствуют"
}

# Установка зависимостей
install_dependencies() {
    log "Проверка наличия Node.js и npm..."
    
    if ! command -v node &> /dev/null; then
        log_error "Node.js не установлен"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm не установлен"
        exit 1
    fi
    
    log "Node.js и npm найдены"
    log "Версия Node.js: $(node --version)"
    log "Версия npm: $(npm --version)"
}

# Установка зависимостей проекта
install_project_dependencies() {
    log "Установка зависимостей проекта..."
    
    cd /opt/feature-factory/app/ui
    
    # Создание бэкапа node_modules если она существует
    if [ -d "node_modules" ]; then
        log "Создание бэкапа node_modules..."
        mv node_modules node_modules.backup.$(date +%s)
    fi
    
    # Установка зависимостей
    if npm install; then
        log "Зависимости успешно установлены"
    else
        log_error "Ошибка при установке зависимостей"
        exit 1
    fi
    
    # Удаление бэкапа если установка прошла успешно
    if [ -d "node_modules.backup.$(date +%s)" ]; then
        rm -rf node_modules.backup.$(date +%s)
    fi
}

# Сборка проекта
build_project() {
    log "Сборка проекта..."
    
    cd /opt/feature-factory/app/ui
    
    # Создание бэкапа dist если она существует
    if [ -d "dist" ]; then
        log "Создание бэкапа dist..."
        mv dist dist.backup.$(date +%s)
    fi
    
    # Сборка проекта
    if npm run build; then
        log "Проект успешно собран"
    else
        log_error "Ошибка при сборке проекта"
        # Восстановление бэкапа
        if [ -d "dist.backup.$(date +%s)" ]; then
            mv dist.backup.$(date +%s) dist
        fi
        exit 1
    fi
    
    # Удаление бэкапа если сборка прошла успешно
    if [ -d "dist.backup.$(date +%s)" ]; then
        rm -rf dist.backup.$(date +%s)
    fi
}

# Копирование файлов в директорию Nginx
copy_files() {
    log "Копирование файлов в директорию Nginx..."
    
    # Создание директории если она не существует
    mkdir -p /var/www/$DOMAIN
    
    # Копирование файлов
    if cp -r /opt/feature-factory/app/ui/dist/* /var/www/$DOMAIN/; then
        log "Файлы успешно скопированы"
    else
        log_error "Ошибка при копировании файлов"
        exit 1
    fi
}

# Настройка прав доступа
set_permissions() {
    log "Настройка прав доступа..."
    
    # Установка прав доступа
    if chown -R www-data:www-data /var/www/$DOMAIN; then
        log "Права доступа успешно установлены"
    else
        log_error "Ошибка при установке прав доступа"
        exit 1
    fi
}

# Настройка Nginx
setup_nginx() {
    log "Настройка Nginx..."
    
    # Копирование конфигурационного файла
    if cp $NGINX_CONFIG /etc/nginx/sites-available/$DOMAIN; then
        log "Конфигурационный файл Nginx скопирован"
    else
        log_error "Ошибка при копировании конфигурационного файла Nginx"
        exit 1
    fi
    
    # Копирование файла .htpasswd если он существует
    if [ -f "$NGINX_HTACCESS" ]; then
        if cp $NGINX_HTACCESS /etc/nginx/.htpasswd; then
            log "Файл .htpasswd скопирован"
        else
            log_error "Ошибка при копировании файла .htpasswd"
            exit 1
        fi
    else
        log_warn "Файл .htpasswd не найден, создание нового файла с учетными данными по умолчанию..."
        # Создание файла с учетными данными ops/ops123
        echo "ops:$apr1$OaFo6Diy$r1JZ07DfD4ni8rMr6t.UF0" > /etc/nginx/.htpasswd
    fi
    
    # Установка прав доступа для .htpasswd
    chmod 644 /etc/nginx/.htpasswd
    chown www-data:www-data /etc/nginx/.htpasswd
    
    # Создание символической ссылки если она не существует
    if [ ! -L "/etc/nginx/sites-enabled/$DOMAIN" ]; then
        if ln -s /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/; then
            log "Символическая ссылка создана"
        else
            log_error "Ошибка при создании символической ссылки"
            exit 1
        fi
    fi
    
    # Проверка конфигурации Nginx
    if nginx -t; then
        log "Конфигурация Nginx проверена успешно"
    else
        log_error "Ошибка в конфигурации Nginx"
        exit 1
    fi
}

# Перезапуск Nginx
restart_nginx() {
    log "Перезапуск Nginx..."
    
    if systemctl reload nginx; then
        log "Nginx успешно перезапущен"
    else
        log_error "Ошибка при перезапуске Nginx"
        exit 1
    fi
}

# Проверка доступности сайта
check_availability() {
    log "Проверка доступности сайта..."
    
    # Ожидание запуска Nginx
    sleep 5
    
    # Проверка доступности
    if curl -s --head https://$DOMAIN | head -n 1 | grep "200 OK" > /dev/null; then
        log "Сайт доступен по адресу https://$DOMAIN"
    else
        log_warn "Не удалось проверить доступность сайта. Проверьте вручную."
    fi
}

# Основная функция
main() {
    log "Начало деплоя UI Feature Factory"
    
    # Проверка прав администратора
    check_sudo
    
    # Определение окружения
    detect_environment
    
    # Проверка наличия необходимых файлов
    check_files
    
    # Установка зависимостей
    install_dependencies
    
    # Установка зависимостей проекта
    install_project_dependencies
    
    # Сборка проекта
    build_project
    
    # Копирование файлов
    copy_files
    
    # Настройка прав доступа
    set_permissions
    
    # Настройка Nginx
    setup_nginx
    
    # Перезапуск Nginx
    restart_nginx
    
    # Проверка доступности сайта
    check_availability
    
    log "Деплой UI Feature Factory завершен успешно"
}

# Запуск основной функции
main "$@"