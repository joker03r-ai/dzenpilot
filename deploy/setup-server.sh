#!/usr/bin/env bash
# Первоначальная настройка сервера под DzenPilot.
# Запускается один раз от имени root:
#   bash deploy/setup-server.sh
#
# Скрипт ничего не удаляет: если Docker или swap уже есть, шаг пропускается.

set -euo pipefail

DEPLOY_PATH="${DEPLOY_PATH:-/opt/dzenpilot}"
SWAP_SIZE="${SWAP_SIZE:-2G}"

log() { echo -e "\n=== $1 ==="; }

if [ "$(id -u)" -ne 0 ]; then
	echo "Запустите скрипт от имени root: sudo bash deploy/setup-server.sh"
	exit 1
fi

log "Обновление списка пакетов"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg rsync git ufw ncdu ripgrep

log "Установка Docker"
if command -v docker >/dev/null 2>&1; then
	echo "Docker уже установлен: $(docker --version)"
else
	install -m 0755 -d /etc/apt/keyrings
	curl -fsSL https://download.docker.com/linux/ubuntu/gpg |
		gpg --dearmor -o /etc/apt/keyrings/docker.gpg
	chmod a+r /etc/apt/keyrings/docker.gpg

	echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
		>/etc/apt/sources.list.d/docker.list

	apt-get update -qq
	apt-get install -y -qq docker-ce docker-ce-cli containerd.io \
		docker-buildx-plugin docker-compose-plugin
	systemctl enable --now docker
	echo "Docker установлен: $(docker --version)"
fi

log "Файл подкачки"
# Сборка Next.js требует памяти. На сервере с 4 ГБ без swap она может не завершиться.
if swapon --show | grep -q '/swapfile'; then
	echo "Swap уже настроен"
else
	fallocate -l "$SWAP_SIZE" /swapfile
	chmod 600 /swapfile
	mkswap /swapfile
	swapon /swapfile
	grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >>/etc/fstab
	echo "Добавлен swap размером $SWAP_SIZE"
fi

log "Фаервол"
ufw allow 22/tcp >/dev/null
ufw allow 80/tcp >/dev/null
ufw allow 443/tcp >/dev/null
ufw --force enable >/dev/null
echo "Открыты порты 22, 80, 443. Остальные закрыты."

log "Каталог проекта"
mkdir -p "$DEPLOY_PATH" "$DEPLOY_PATH/backups"
echo "Каталог: $DEPLOY_PATH"

log "Автоматическая очистка Docker"
cat >/etc/cron.weekly/docker-prune <<'CRON'
#!/bin/sh
docker image prune -af --filter "until=168h" >/dev/null 2>&1
docker builder prune -af --filter "until=168h" >/dev/null 2>&1
CRON
chmod +x /etc/cron.weekly/docker-prune

log "Готово"
cat <<INFO

Сервер подготовлен. Осталось создать файл с настройками:

  cd $DEPLOY_PATH
  cp .env.example .env
  bash deploy/generate-secrets.sh    # подставит случайные пароли и ключи
  nano .env                          # впишите SITE_ADDRESS и, если нужно, ключ Anthropic

После этого запустите:

  docker compose -f docker-compose.prod.yml up -d --build

INFO
