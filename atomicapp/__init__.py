import logging

def set_logging(name="atomicapp", level=logging.DEBUG):
    # create logger
    logger = logging.getLogger(name)
    logger.handlers = []
    logger.setLevel(level)

    # create console handler
    ch = logging.StreamHandler()

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)


set_logging(level=logging.DEBUG) #override this however you want
