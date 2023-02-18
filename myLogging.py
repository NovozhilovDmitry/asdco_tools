import logging
import os

# Set main logger
LOGGING_LOG_FILE = 'logger.log'
LOGGING_FORMATTER_STRING = r'%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.INFO)
stream_handler_format = logging.Formatter(LOGGING_FORMATTER_STRING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(stream_handler_format)
file_handler_format = logging.Formatter(LOGGING_FORMATTER_STRING)
file_handler = logging.FileHandler(LOGGING_LOG_FILE)
file_handler.setFormatter(file_handler_format)
file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)
logger.addHandler(file_handler)
if os.environ.get('PYTHON_LOG_LEVEL') == 'debug':
    logger.setLevel(logging.DEBUG)
