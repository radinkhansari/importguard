import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

database_url = URL.create(
    drivername="postgresql+psycopg",
    username="importguard",
    password=os.environ["POSTGRES_PASSWORD"],
    host="127.0.0.1",
    port=5433,
    database="importguard",
)

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 5},
)

if __name__ == "__main__":
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar_one()
        print(f"Database connection successful! Result: {result}")