import os
from pydantic import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):

    load_dotenv()
    
    # ESIGHT ENV
    ESIGHT_USERNAME: str = os.getenv("ESIGHT_USER")
    ESIGHT_PASSWORD: str = os.getenv("ESIGHT_PASS")
    ESIGHT_LOCATION: str = os.getenv("ESIGHT_URL")

    # KAFKA ENV
    KAFKA_LOCATION: str = os.getenv("KAFKA_URL")

config = Settings()
