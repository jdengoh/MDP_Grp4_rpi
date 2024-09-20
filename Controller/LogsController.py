import logging

def event_logger() -> logging.Logger:

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not logger.hasHandlers():

        # console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)

        # file handler
        fh = logging.FileHandler('events.log')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)

        # add handlers to logger
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger