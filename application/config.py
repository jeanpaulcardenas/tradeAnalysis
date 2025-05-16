import logging


DEBUG = False


def get_logger(name:str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler('./test.log', mode='w')
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger