#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log(){ echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn(){ echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error(){ echo -e "${RED}[ERROR]${NC} $*"; }

check_sudo(){ [ "$EUID" -eq 0 ] || { log_error "Нужно sudo/root"; exit 1; }; }

detect_environment(){
  # Почитаем принудительные значения (если заданы)
  local want_env="${FF_ENV:-}"
  local want_domain="${FF_DOMAIN:-}"

  if [[ -n "$want_env" ]]; then
    case "$want_env" in
      tst|test) ENV="test" ;;
      prod)     ENV="prod" ;;
      *)        log_error "Неизвестный FF_ENV='$want_env' (ожидалось prod|tst|test)"; exit 1 ;;
    esac
  elif [[ -f /etc/default/feature-factory-test ]]; then
    ENV="test"
  elif [[ -f /etc/default/feature-factory-prod ]]; then
    ENV="prod"
  else
    log_error "Не удалось определить окружение (нет /etc/default/feature-factory-*) и не задан FF_ENV"
    exit 1
  fi

  if [[ "$ENV" == "test" ]]; then
    CONFIG_FILE="/etc/default/feature-factory-test"
    DOMAIN="${want_domain:-etl-tst.chococraft.ru}"
    NGINX_CONFIG="/opt/feature-factory/configs/nginx/etl-tst.chococraft.ru"
  else
    CONFIG_FILE="/etc/default/feature-factory-prod"
    DOMAIN="${want_domain:-etl.chococraft.ru}"
    NGINX_CONFIG="/opt/feature-factory/configs/nginx/etl.chococraft.ru"
  fi

  log "Обнаружено окружение: $ENV"
  log "Домен: $DOMAIN"
  log "Конфиг Nginx: $NGINX_CONFIG"
}

check_files(){
  [[ -d /opt/feature-factory/app/ui ]] || { log_error "Нет каталога UI"; exit 1; }
  [[ -f "$NGINX_CONFIG" ]] || { log_error "Нет файла Nginx-конфига: $NGINX_CONFIG"; exit 1; }
  log "Все необходимые файлы присутствуют"
}

install_dependencies(){
  command -v node >/dev/null || { log_error "Node.js не установлен"; exit 1; }
  command -v npm  >/dev/null || { log_error "npm не установлен"; exit 1; }
  log "Node.js: $(node -v) / npm: $(npm -v)"
}

install_project_dependencies(){
  log "Установка зависимостей проекта…"
  cd /opt/feature-factory/app/ui
  TS=$(date +%s)

  if [[ -d node_modules ]]; then
    log "Создание бэкапа node_modules…"
    mv node_modules "node_modules.backup.$TS"
  fi

  if [[ -f package-lock.json ]]; then
    if ! npm ci; then
      log_warn "npm ci неуспешен — пробую npm install"
      npm install || { log_error "npm install неуспешен"; exit 1; }
    fi
  else
    npm install || { log_error "npm install неуспешен"; exit 1; }
  fi

  [[ -d "node_modules.backup.$TS" ]] && rm -rf "node_modules.backup.$TS"
  log "Зависимости успешно установлены"
}

build_project(){
  log "Сборка проекта…"
  cd /opt/feature-factory/app/ui
  TS=${TS:-$(date +%s)}
  if [[ -d dist ]]; then
    log "Создание бэкапа dist…"
    mv dist "dist.backup.$TS"
  fi

  npm run build || {
    log_error "Сборка неуспешна"; [[ -d "dist.backup.$TS" ]] && mv "dist.backup.$TS" dist; exit 1;
  }
  [[ -d "dist.backup.$TS" ]] && rm -rf "dist.backup.$TS"
  log "Проект успешно собран"
}

copy_files(){
  log "Копирование в /var/www/$DOMAIN…"
  mkdir -p "/var/www/$DOMAIN"
  cp -r /opt/feature-factory/app/ui/dist/* "/var/www/$DOMAIN/" || { log_error "Копирование неуспешно"; exit 1; }
  chown -R www-data:www-data "/var/www/$DOMAIN"
  log "Файлы скопированы и права выставлены"
}

setup_basic_auth(){
  log "Настройка Basic Auth (.htpasswd)…"
  local HTPASSWD="/etc/nginx/.htpasswd"
  if [[ -f "$HTPASSWD" ]]; then
    log "Найден существующий .htpasswd — пропускаю генерацию"
    return
  fi
  local USER="${FF_UI_BASIC_AUTH_USER:-ops}"
  local PASS="${FF_UI_BASIC_AUTH_PASS:-}"
  if [[ -z "$PASS" ]]; then
    if command -v openssl >/dev/null; then
      PASS=$(openssl rand -base64 18 | tr -d \' =+/\\n\' | cut -c1-20)
    else
      PASS=$(date +%s | sha256sum | head -c20)
    fi
  fi
  if command -v htpasswd >/dev/null; then
    htpasswd -bc "$HTPASSWD" "$USER" "$PASS"
  else
    command -v openssl >/dev/null || { log_error "Нет htpasswd/openssl"; exit 1; }
    HASH=$(openssl passwd -apr1 "$PASS"); echo "$USER:$HASH" > "$HTPASSWD"
  fi
  chmod 640 "$HTPASSWD"; chown root:www-data "$HTPASSWD"
  local CREDS="/root/.ff_ui_basic_auth_${ENV}.txt"
  umask 077; {
    echo "UI Basic Auth ($ENV):"
    echo "  user: $USER"
    echo "  pass: $PASS"
  } > "$CREDS"; umask 022
  log_warn "Сгенерированы креды Basic Auth → $CREDS"
}

setup_nginx(){
  log "Настройка Nginx…"
  # Бэкап текущего конфига перед заменой
  if [[ -f "/etc/nginx/sites-available/$DOMAIN" ]]; then
    cp "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-available/$DOMAIN.backup.$(date +%Y%m%d_%H%M%S)"
  fi
  cp "$NGINX_CONFIG" "/etc/nginx/sites-available/$DOMAIN"
  [[ -L "/etc/nginx/sites-enabled/$DOMAIN" ]] || ln -s "/etc/nginx/sites-available/$DOMAIN" /etc/nginx/sites-enabled/

  # Если деплоим test и prod-виртуал включен без валидного серта — временно отключим, чтобы nginx -t не падал
  if [[ "$ENV" == "test" ]] && [[ -L /etc/nginx/sites-enabled/etl.chococraft.ru ]] && [[ ! -f /etc/ssl/certs/etl.chococraft.ru.crt ]]; then
    log_warn "Отключаю prod vhost: нет /etc/ssl/certs/etl.chococraft.ru.crt"
    unlink /etc/nginx/sites-enabled/etl.chococraft.ru || true
  fi

  nginx -t || { log_error "Ошибка в конфигурации Nginx"; exit 1; }
  log "Конфигурация Nginx проверена успешно"
}

restart_nginx(){
  log "Перезапуск Nginx…"
  systemctl reload nginx || { log_error "Не удалось перезапустить Nginx"; exit 1; }
  log "Nginx успешно перезапущен"
}

check_availability(){
  log "Проверка доступности https://$DOMAIN …"
  sleep 2
  if curl -fsI "https://$DOMAIN" >/dev/null; then
    log "Сайт доступен"
  else
    log_warn "Не удалось подтвердить доступность — проверь вручную"
  fi
}

main(){
  log "Начало деплоя UI Feature Factory"
  check_sudo
  detect_environment
  check_files
  install_dependencies
  install_project_dependencies
  build_project
  copy_files
  setup_basic_auth
  setup_nginx
  restart_nginx
  check_availability
}

main "$@"