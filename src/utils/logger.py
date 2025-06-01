import logging
import sys

# Configure the logger
LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGING_LEVEL = logging.INFO # Default to INFO, can be changed

def get_logger(name: str, level: int = LOGGING_LEVEL) -> logging.Logger:
    """
    Creates and configures a logger instance.

    Args:
        name: The name for the logger (usually __name__ of the calling module).
        level: The logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if logger is already configured
    if not logger.handlers:
        # Create a console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter(LOGGING_FORMAT)
        console_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(console_handler)

    return logger

# Example usage (can be removed or kept for direct testing of this module)
if __name__ == '__main__':
    test_logger = get_logger('MyTestApp', logging.DEBUG)
    test_logger.debug('This is a debug message.')
    test_logger.info('This is an info message.')
    test_logger.warning('This is a warning message.')
    test_logger.error('This is an error message.')
    test_logger.critical('This is a critical message.')
