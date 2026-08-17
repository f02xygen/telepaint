import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from bot.bot_instance import init_bot, dp
from bot.handlers import router as bot_router
from bot.background import periodic_sync_task
from database import init_db
from web.app import web_app

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    bot = init_bot()
    dp.include_router(bot_router)
    
    # handle_signals=False отключает перехват SIGINT ботом, 
    # отдавая управление завершением Uvicorn'у
    bot_task = asyncio.create_task(dp.start_polling(bot, handle_signals=False))
    bg_task = asyncio.create_task(periodic_sync_task(bot))
    
    logging.info("🚀 Приложение и бот успешно запущены!")
    yield
    
    # Корректно отменяем задачи и дожидаемся их завершения
    bot_task.cancel()
    bg_task.cancel()
    
    await asyncio.gather(bot_task, bg_task, return_exceptions=True)
    await bot.session.close()
    logging.info("👋 Завершение работы выполнено успешно.")

app = FastAPI(lifespan=lifespan)
app.mount("/", web_app)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)