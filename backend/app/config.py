import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_host: str = os.getenv("DATABASE_HOST", "localhost")
    connection_str: str = f"postgresql://postgres:postgres@{database_host}:5432/vector_db"
    index_table: str = "ajua_demo_hybrid_search"
    embed_dim: int = 3072


config = Settings()
