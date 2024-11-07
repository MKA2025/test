from typing import Dict, Any
from dataclasses import dataclass
from pathlib import Path
import json

@dataclass
class ConfigValidationError:
    field: str
    message: str

class ConfigValidator:
    def __init__(self, config_path: str = 'config.json'):
        self.config_path = Path(config_path)
        self.required_fields = {
            'bot_token': str,
            'download_path': str,
            'max_downloads': int,
            'allowed_formats': list,
            'quality_options': dict
        }

    def validate_config(self) -> list[ConfigValidationError]:
        """Validate configuration file"""
        errors = []
        
        if not self.config_path.exists():
            return [ConfigValidationError('config', 'Configuration file not found')]

        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError:
            return [ConfigValidationError('config', 'Invalid JSON format')]

        for field, field_type in self.required_fields.items():
            if field not in config:
                errors.append(ConfigValidationError(field, 'Required field missing'))
            elif not isinstance(config[field], field_type):
                errors.append(ConfigValidationError(
                    field, 
                    f'Invalid type. Expected {field_type.__name__}'
                ))

        return errors

    def create_default_config(self):
        """Create default configuration file"""
        default_config = {
            'bot_token': '',
            'download_path': 'downloads',
            'max_downloads': 3,
            'allowed_formats': ['mp3', 'flac', 'm4a'],
            'quality_options': {
                'low': '128k',
                'medium': '256k',
                'high': '320k',
                'lossless': 'flac'
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
