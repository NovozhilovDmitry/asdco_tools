import logging

LOGGING_LOG_FILE = 'logger.log'
LOGGING_FORMATTER_STRING = r'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(LOGGING_LOG_FILE, mode='a')
formatter = logging.Formatter(LOGGING_FORMATTER_STRING)
handler.setFormatter(formatter)
logger.addHandler(handler)
