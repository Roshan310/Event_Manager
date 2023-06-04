from pydantic import BaseSettings

class Setting(BaseSettings):
    database_name: str
    database_port: str
    database_username: str
    database_password: str
    database_hostname: str
    algorithm: str
    jwt_secret_key: str
    access_token_expires_minutes:int

    class Config:
        env_file = ".env"

settings = Setting()
