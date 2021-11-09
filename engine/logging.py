from pyshipt_logging.logger import ShiptLogging

logger = ShiptLogging.get_logger(name="bundle-engine")
logger.propagate = False
