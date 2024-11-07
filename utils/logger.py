import logging
from logging.handlers import RotatingFileHandler
import sys
from pathlib import Path

class BotLogger:
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )

        # Create handlers
        file_handler = RotatingFileHandler(
            self.log_dir / 'bot.log',
            maxBytes=1024*1024,  # 1MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)

        # Setup logger
        self.logger = logging.getLogger('MusicDownloaderBot')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger
