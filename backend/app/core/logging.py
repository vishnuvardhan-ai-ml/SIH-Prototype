"""
Logging Configuration.
"""
import logging
import sys
from backend.app.core.config import settings


def setup_logging():
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Silence overly verbose external loggers if needed
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


logger = logging.getLogger("sih_backend")
