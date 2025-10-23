# env.py
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class EnvConfig:
    def __init__(self, env_file=".env"):
        self._env_file = Path(env_file)
        self._load_env()
    
    def _load_env(self):
        """Load environment variables from .env file"""
        if self._env_file.exists():
            with open(self._env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    def get(self, key, default=None):
        """Get environment variable"""
        return os.environ.get(key, default)
    
    def get_baidu_ocr_config(self):
        """Get Baidu OCR configuration"""
        return {
            'api_key': self.get('BAIDU_OCR_API_KEY'),
        }
    
    def get_deepseek_config(self):
        """Get DeepSeek configuration"""
        return {
            'api_key': self.get('DEEPSEEK_API_KEY')
        }
    
    def get_amap_config(self):
        """Get AMAP configuration"""
        return {
            'api_key': self.get('AMAP_API_KEY')
        }
    
    def get_wxauto_config(self):
        """Get DeepSeek configuration"""
        return {
            'api_key': self.get('WXAUTO_API_KEY'),
            'api_url': self.get('WXAUTO_API_URL'),
            'download_path': self.get('WXAUTO_DOWNLOAD_PATH')
        }

    def get_mitv_config(self):
        """Get MiTv configuration"""
        return {
            'ip': self.get('MITV_IP')
        }
    
    def get_printer_config(self):
        """Get IPP configuration"""
        return {
            'name': self.get('PRINTER_NAME')
        }
    
    def get_qb_location_config(self):
        """Get QB Location Configuration"""
        return {
            'url': self.get('QB_LOCATION_URL'),
            'authority': self.get('QB_LOCATION_AUTHORITY'),
            'username': self.get('QB_LOCATION_USERNAME'),
            'password': self.get('QB_LOCATION_PASSWORD')
        }

    def get_db_config(self):
        return {
            'path': self.get('SQLLITE_DB_PATH'),
        }

# Test function
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    config = EnvConfig()
    
    baidu_config = config.get_baidu_ocr_config()
    deepseek_config = config.get_deepseek_config()
    wxauto_config = config.get_wxauto_config()
    
    logger.info("Baidu OCR Config:")
    logger.info(f"API Key: {baidu_config['api_key']}" if baidu_config['api_key'] else "Not set")
    
    logger.info("DeepSeek Config:")
    logger.info(f"API Key: {deepseek_config['api_key']}" if deepseek_config['api_key'] else "Not set")

    logger.info("WXAuto Config:")
    logger.info(f"API Url: {wxauto_config['api_url']}" if wxauto_config['api_url'] else "Not set")
    logger.info(f"API Key: {wxauto_config['api_key']}" if wxauto_config['api_key'] else "Not set")
