# Автодеплой DzenPilot

Каждый коммит в ветку `main` запускает GitHub Actions: сначала тесты,
затем обновление сервера. Если тесты не прошли, деплой не начинается —
на сервер не попадёт заведомо сломанный код.

```
git push → тесты (Postgres + Redis) → rsync на сервер
         → docker compose up -d --build → проверка /health
```

## Что нужно настроить один раз

### 1. Секреты репозитория на GitHub

**Settings → Secrets and variables → Actions → New repository secret**

| Имя | Значение | Обязательный |
|-----|----------|--------------|
| `SSH_HOST` | `45.144.29.75` | да |
| `SSH_USER` | `root` | да |
| `SSH_PRIVATE_KEY` | содержимое файла `~/.ssh/github_actions_deploy` целиком | да |
| `SSH_PORT` | `22` | нет, по умолчанию 22 |
| `DEPLOY_PATH` | `/opt/dzenpilot` | нет, значение по умолчанию |

Приватный ключ копируется из файла на вашем компьютере. Он должен начинаться
строкой `-----BEGIN OPENSSH PRIVATE KEY-----` и заканчиваться
`-----END OPENSSH PRIVATE KEY-----`, включая обе эти строки и перевод строки в конце.

### 2. Публичный ключ на сервере

Публичная часть ключа GitHub Actions должна лежать в `~/.ssh/authorized_keys`
на сервере, иначе Actions не сможет подключиться.

### 3. Подготовка сервера

```bash
ssh root@45.144.29.75
git clone git@github.com:ВАШ_ЛОГИН/dzenpilot.git /opt/dzenpilot
cd /opt/dzenpilot
bash deploy/setup-server.sh
cp .env.example .env
bash deploy/generate-secrets.sh
nano .env      # укажите SITE_ADDRESS
docker compose -f docker-compose.prod.yml up -d --build
```

Файл `.env` создаётся один раз вручную и при деплое не перезаписывается —
боевые пароли и ключи не хранятся в репозитории.

## Что происходит при каждом деплое

1. **Тесты.** Поднимаются PostgreSQL и Redis, применяются миграции, запускается
   `pytest`, проверяются типы TypeScript и собирается фронтенд.
2. **Копирование.** `rsync` переносит файлы в `/opt/dzenpilot`. Исключаются
   `.env`, `.git`, `node_modules`, `.next` и кэш Python.
3. **Резервная копия.** Перед перезапуском создаётся дамп базы в
   `/opt/dzenpilot/backups/`. Хранятся последние 10 копий.
4. **Пересборка.** `docker compose up -d --build` обновляет только изменившиеся
   образы. Миграции применяются автоматически при старте backend.
5. **Проверка.** Actions ждёт до 200 секунд ответа от `/health`. Если сервис
   не поднялся, деплой отмечается как неуспешный и в лог выводятся последние
   80 строк журналов контейнеров.

## Полезные команды на сервере

```bash
cd /opt/dzenpilot

# Состояние сервисов
docker compose -f docker-compose.prod.yml ps

# Журналы
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend

# Перезапуск одного сервиса
docker compose -f docker-compose.prod.yml restart backend

# Ручное применение миграций
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Резервная копия базы прямо сейчас
docker exec dzenpilot_postgres pg_dumpall -U dzenpilot > backups/manual-$(date +%F).sql
```

## Откат к предыдущей версии

```bash
cd /opt/dzenpilot
git log --oneline -10
git checkout <хеш нужного коммита>
docker compose -f docker-compose.prod.yml up -d --build
```

Восстановление базы из копии:

```bash
cat backups/before-deploy-20260725-120000.sql |
  docker exec -i dzenpilot_postgres psql -U dzenpilot -d postgres
```

## Частые ошибки

| Сообщение | Причина и решение |
|-----------|-------------------|
| `Permission denied (publickey)` | Публичный ключ Actions не добавлен в `~/.ssh/authorized_keys` на сервере |
| `ОШИБКА: на сервере нет файла .env` | Выполните на сервере `cp .env.example .env` и `bash deploy/generate-secrets.sh` |
| Сборка фронтенда падает по памяти | Проверьте swap: `swapon --show`. Скрипт `setup-server.sh` добавляет 2 ГБ |
| `/health` не отвечает | Смотрите `docker compose -f docker-compose.prod.yml logs backend` |
| Сертификат не выпускается | Домен должен указывать на IP сервера, порты 80 и 443 должны быть открыты |

## Безопасность

- Приватные ключи не хранятся в репозитории и не выводятся в журналы Actions —
  GitHub автоматически скрывает значения секретов.
- PostgreSQL и Redis не публикуют порты наружу, доступ только внутри сети Docker.
- На боевом сервере `COOKIE_SECURE=true`, поэтому вход работает только по HTTPS.
  При работе по голому IP используйте `SITE_ADDRESS=:80` и `COOKIE_SECURE=false`,
  но это временный режим — для реальной работы нужен домен.
- Ключ шифрования `APP_ENCRYPTION_KEY` менять нельзя: после смены сохранённые
  ключи интеграций перестанут расшифровываться, их придётся вводить заново.
