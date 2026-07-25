#!/usr/bin/env bash
# Подставляет в .env случайные пароль базы, SECRET_KEY и ключ шифрования.
# Запускается на сервере один раз после копирования .env.example в .env.
#
#   bash deploy/generate-secrets.sh
#
# Повторный запуск ничего не ломает: уже заполненные значения не трогаются.

set -euo pipefail

ENV_FILE="${ENV_FILE:-.env}"

if [ ! -f "$ENV_FILE" ]; then
	echo "Файл $ENV_FILE не найден. Сначала выполните: cp .env.example .env"
	exit 1
fi

PLACEHOLDERS="change_me_postgres|replace_me_with_a_long_random_string|replace_me_with_a_fernet_key"

set_value() {
	local key="$1" value="$2"
	local current
	current="$(grep -E "^${key}=" "$ENV_FILE" | head -1 | cut -d= -f2- || true)"

	if [ -n "$current" ] && ! echo "$current" | grep -qE "^(${PLACEHOLDERS})$"; then
		echo "  $key — уже задан, пропускаю"
		return
	fi

	# Экранируем символы, значимые для sed
	local escaped
	escaped="$(printf '%s' "$value" | sed -e 's/[\/&|]/\\&/g')"
	if grep -qE "^${key}=" "$ENV_FILE"; then
		sed -i -E "s|^${key}=.*|${key}=${escaped}|" "$ENV_FILE"
	else
		echo "${key}=${value}" >>"$ENV_FILE"
	fi
	echo "  $key — сгенерирован"
}

echo "Генерация секретов в $ENV_FILE:"

POSTGRES_PASSWORD="$(openssl rand -hex 24)"
SECRET_KEY="$(openssl rand -base64 64 | tr -d '\n=' | tr '+/' '-_')"
# Fernet требует ровно 32 байта в base64 с URL-безопасным алфавитом
APP_ENCRYPTION_KEY="$(openssl rand -base64 32 | tr '+/' '-_')"

set_value POSTGRES_PASSWORD "$POSTGRES_PASSWORD"
set_value SECRET_KEY "$SECRET_KEY"
set_value APP_ENCRYPTION_KEY "$APP_ENCRYPTION_KEY"

# Боевые значения, отличающиеся от режима разработки
sed -i -E 's|^APP_ENV=.*|APP_ENV=production|' "$ENV_FILE"
sed -i -E 's|^APP_DEBUG=.*|APP_DEBUG=false|' "$ENV_FILE"
sed -i -E 's|^COOKIE_SECURE=.*|COOKIE_SECURE=true|' "$ENV_FILE"
sed -i -E 's|^SEED_DEMO_DATA=.*|SEED_DEMO_DATA=false|' "$ENV_FILE"

chmod 600 "$ENV_FILE"

cat <<'INFO'

Готово. Осталось проверить вручную в .env:

  SITE_ADDRESS       — ":80" для работы по IP или "ваш-домен.ру" для HTTPS
  NEXT_PUBLIC_API_URL — оставьте пустым, запросы идут через тот же домен
  ANTHROPIC_API_KEY  — можно оставить пустым и ввести ключ
                        в интерфейсе, в разделе «Интеграции»

Важно: файл .env не попадает в GitHub и не перезаписывается при деплое.
Сделайте его резервную копию в надёжном месте — при потере APP_ENCRYPTION_KEY
сохранённые ключи интеграций расшифровать будет невозможно.
INFO
