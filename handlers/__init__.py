from aiogram import Router


def setup_routers() -> Router:
    from . import admin, report, settings, streamer, user

    router = Router()

    # Подключаем все роутеры
    router.include_router(user.router)
    router.include_router(admin.router)
    router.include_router(report.router)
    router.include_router(settings.router)
    router.include_router(streamer.router)

    return router