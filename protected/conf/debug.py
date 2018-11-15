# -*- coding: utf-8 -*-
import logging
LOG_FILE = 'debugs.log'
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes = 1024*1024, backupCount=5)
fmt = '%(asctime)s-%(filename)s:%(lineno)s-%(name)s-%(levelname)s-%(message)s'
formatter = logging.Formatter(fmt)
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info('info msg')