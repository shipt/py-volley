from pyshipt_logging.logger import ShiptLogging

logger = ShiptLogging.get_logger(name="volley")
logger.propagate = False
