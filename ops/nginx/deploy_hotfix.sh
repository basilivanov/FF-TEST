#!/usr/bin/env bash
set -euo pipefail

SITE=etl-tst.chococraft.ru
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
NEW_CONF="$SRC_DIR/sites-available/${SITE}.hotfix"
TARGET="/etc/nginx/sites-available/${SITE}"
BACKUP="/etc/nginx/sites-available/${SITE}.bak-$(date +%F-%H%M%S)"

echo "[i] Backing up current config to $BACKUP"
sudo cp -a "$TARGET" "$BACKUP"

echo "[i] Installing new config from $NEW_CONF"
sudo install -o feature -g feature -m 0644 "$NEW_CONF" "$TARGET"

echo "[i] Syntax check (nginx -t)"
sudo nginx -t

echo "[i] Reloading nginx"
sudo systemctl reload nginx

echo "[ok] Deployed. To rollback: sudo cp -a $BACKUP $TARGET && sudo nginx -t && sudo systemctl reload nginx"
