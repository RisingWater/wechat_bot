# deepseek.py
import requests
import json
from PIL import Image
import os
import logging
from env import EnvConfig

logger = logging.getLogger(__name__)

class AmapAPI:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._api_key = None
        self._load_config()

    def _load_config(self):
        """Load AMAP configuration from environment"""
        amap_config = self._config.get_amap_config()
        self._api_key = amap_config.get('api_key')
        
        if not self._api_key:
            logger.warning("AMAP API key not found in environment")
        else:
            logger.info("AMAP configuration loaded successfully")

    def get_amap_static_image(self, longitude, latitude, zoom=17, size='800*800', markers_style='mid,,A', save_path=None):
        """
        使用高德地图静态图API获取地图图片
        
        Args:
            longitude: 经度
            latitude: 纬度
            zoom: 缩放级别 (1-18)
            size: 图片尺寸，如 '400*400'
            markers_style: 标记样式
            save_path: 图片保存路径
            api_key: 高德地图API密钥
        
        Returns:
            str: 保存的文件路径，失败返回None
        """
        if not self._api_key:
            print("请提供高德地图API密钥")
            return None
        
        url = "https://restapi.amap.com/v3/staticmap"
        
        params = {
            'location': f'{longitude},{latitude}',
            'zoom': zoom,
            'size': size,
            'markers': f'{markers_style}:{longitude},{latitude}',
            'key': self._api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            print(f"地图API状态码: {response.status_code}")
            
            if response.status_code == 200:
                # 如果没有指定保存路径，生成默认路径
                if not save_path:
                    save_path = f"map_{longitude}_{latitude}.png"
                
                # 确保目录存在
                os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
                
                # 保存图片
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"地图图片已保存: {save_path}")
                
                # 验证图片是否有效
                try:
                    image = Image.open(save_path)
                    print(f"图片尺寸: {image.size}")
                    image.close()
                except Exception as e:
                    print(f"图片验证失败: {e}")
                    return None
                    
                return save_path
            else:
                print(f"请求失败: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"获取地图图片失败: {e}")
            return None
        except Exception as e:
            print(f"保存图片失败: {e}")
            return None

