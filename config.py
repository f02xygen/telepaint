from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_IDS: str
    CHANNEL_ID: str
    BASE_URL: str = "http://localhost:8000"

    EXPIRE_SECONDS: int = 86400
    SYNC_INTERVAL: int = 30

    USE_PROXY: bool = False
    SOCKS5_PROXY: str = "socks5://127.0.0.1:1080"

    @property
    def admin_ids_set(self) -> set[int]:
        """Возвращает set с ID админов"""
        return {int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()}
    
    class Config:
        env_file = ".env"

settings = Settings()