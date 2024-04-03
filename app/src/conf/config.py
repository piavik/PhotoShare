import cloudinary
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    sqlalchemy_database_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_from_name: str
    redis_host: str
    redis_port: int
    redis_user: str
    redis_pass: str
    cloudinary_name: str
    cloudinary_api_key: str
    cloudinary_api_secret: str
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()


cloudinary_config = cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )