"""Сборка всех маршрутов API."""

from fastapi import APIRouter

from app.api.v1 import ai, auth, integrations, jobs, notifications, projects

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Авторизация"])
api_router.include_router(projects.router, prefix="/projects", tags=["Проекты"])
api_router.include_router(integrations.router, prefix="/projects", tags=["Интеграции"])
api_router.include_router(ai.router, prefix="/ai", tags=["ИИ"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Фоновые задачи"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Уведомления"])
