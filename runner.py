import os
import time
from loguru import logger

while 1:
    out = os.system("python trigger_photo_cron.py")
    if out != 0:
        raise Exception(out)
    else:
        logger.info("Runner ok")
    time.sleep(60*5)
