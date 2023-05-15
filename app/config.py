import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    LOCAL: bool = 0
    BASE_DIR: str = None
    MEiDE = 111000
    PORT: int
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_PORT: int
    SPEED = 5000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.BASE_DIR = os.path.curdir if self.LOCAL else "/project/app"

    @property
    def DB_CONN_URL(self):
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


settings = Settings()
