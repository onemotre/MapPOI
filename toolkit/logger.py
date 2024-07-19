import os
import logging

import config


def set_up_logger(name: str, level: object = logging.ERROR) -> object:
    log_dirname = config.settings.BASE_FILE_PATH.LOG_PATH.value + config.settings.BASE_FILE_PATH.DIV.value
    if not os.path.exists(log_dirname):
        os.makedirs(log_dirname)
    log_file = os.path.join(log_dirname, f"{name}.log")
    formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level=level)
    logger.addHandler(handler)

    return logger


clients_log = set_up_logger("Client_logger")
collector_log = set_up_logger("Collector_logger")

if __name__ == "__main__":
    set_up_logger("Test_logger")
