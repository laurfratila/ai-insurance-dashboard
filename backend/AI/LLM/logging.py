import logging
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

rag_logger = logging.getLogger("rag_logger")
rag_logger.setLevel(logging.INFO)

if not rag_logger.handlers:
    file_handler = logging.FileHandler(os.path.join(LOG_DIR, "rag.log"), mode="a")
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    rag_logger.addHandler(file_handler)
