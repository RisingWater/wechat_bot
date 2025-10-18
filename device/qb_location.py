import requests
import logging
import device.coord_transfrom as coord_transfrom
from env import EnvConfig

logger = logging.getLogger(__name__)

class QBLocation:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._load_config()
        self._session = requests.Session()
        self._token = None
        self._setup_headers()

    def _load_config(self):
        """Load QB Location configuration from environment"""
        qb_location_config = self._config.get_qb_location_config()
        self._base_url = qb_location_config.get('url')
        self._username = qb_location_config.get('username')
        self._password = qb_location_config.get('password')
        self._authority = qb_location_config.get('authority')
        
    def _setup_headers(self):
        """设置基础请求头"""
        self.base_headers = {
            "authority": self._authority,
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "client_type": "pc",
            "content-type": "application/json",
            "origin": self._base_url,
            "priority": "u=1, i",
            "referer": f"{self._base_url}/login",
            "sec-ch-ua": '"Microsoft Edge";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0"
        }
        self._session.headers.update(self.base_headers)
    
    def _update_token_header(self):
        """更新header中的token"""
        if self._token:
            self._session.headers.update({"token": self._token})
    
    def _login(self):
        """
        登录并返回token
        
        Args:
            login_name: 登录名
            password: 密码
            
        Returns:
            str: token字符串，登录失败返回None
        """
        url = f"{self._base_url}/api/sys/loginout/login"
        
        payload = {
            "loginName": self._username,
            "password": self._password
        }
        
        try:
            response = self._session.post(
                url=url,
                json=payload,
                timeout=10
            )
            
            logger.info(f"登录状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                # 根据实际响应结构提取token
                if response_data.get("code") == 1000:  # 操作成功
                    token = response_data.get("data", {}).get("token")
                    if token:
                        self._token = token
                        self._update_token_header()  # 更新header中的token
                        logger.info("登录成功！")
                        return token
                    else:
                        logger.error("响应中未找到token字段")
                        return None
                else:
                    error_msg = response_data.get("msg", "未知错误")
                    logger.error(f"登录失败: {error_msg}")
                    return None
            else:
                logger.error(f"登录请求失败，状态码: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"登录请求发生错误: {e}")
            return None
        except Exception as e:
            logger.error(f"登录发生未知错误: {e}")
            return None
    
    def _get_device_list(self, size=100, current=1, state_type="", imei="", office_id="", exclude_lbs=0):
        """
        获取设备列表
        
        Args:
            size: 每页大小
            current: 当前页码
            state_type: 状态类型
            imei: 设备IMEI
            office_id: 办公室ID
            exclude_lbs: 是否排除LBS
            
        Returns:
            dict: 设备列表数据，请求失败返回None
        """
        if not self._token:
            logger.info("请先登录获取token")
            return None
            
        url = f"{self._base_url}/api/device/locationManager/getOfficeDeviceTreeData"
        
        params = {
            "size": size,
            "current": current,
            "stateType": state_type,
            "imei": imei,
            "officeId": office_id,
            "excludeLbs": exclude_lbs
        }
        
        try:
            response = self._session.get(
                url=url,
                params=params,
                timeout=10
            )
            
            logger.info(f"获取设备列表状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("code") == 1000:  # 操作成功
                    logger.info("获取设备列表成功！")
                    return response_data.get("data", {})
                else:
                    error_msg = response_data.get("msg", "未知错误")
                    logger.error(f"获取设备列表失败: {error_msg}")
                    return None
            else:
                logger.error(f"获取设备列表请求失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取设备列表请求发生错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取设备列表发生未知错误: {e}")
            return None
        
    def _get_curr_point_info_all(self, device_id_list, exclude_lbs=1):
        """
        获取设备当前位置详细信息
        
        Args:
            device_id_list: 设备ID列表，如 [159020]
            exclude_lbs: 是否排除LBS，默认1
            
        Returns:
            list: 设备详细信息列表，请求失败返回None
        """
        if not self._token:
            logger.info("请先登录获取token")
            return None
            
        url = f"{self._base_url}/api/device/locationManager/getCurrPointInfoAll"
        
        payload = {
            "deviceIdList": device_id_list,
            "excludeLbs": exclude_lbs
        }
        
        try:
            response = self._session.post(
                url=url,
                json=payload,
                timeout=10
            )
            
            logger.info(f"获取设备详情状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("code") == 1000:  # 操作成功
                    logger.info("获取设备详情成功！")
                    return response_data.get("data", [])
                else:
                    error_msg = response_data.get("msg", "未知错误")
                    logger.error(f"获取设备详情失败: {error_msg}")
                    return None
            else:
                logger.error(f"获取设备详情请求失败，状态码: {response.status_code}")
                logger.error(f"响应内容: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取设备详情请求发生错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取设备详情发生未知错误: {e}")
            return None

    def _get_model_id(self, device_id):
        """
        便捷方法：获取设备的modelId
        
        Args:
            device_id: 设备ID
            
        Returns:
            int: modelId，获取失败返回None
        """
        device_info_list = self.get_curr_point_info_all([device_id])
        if device_info_list and len(device_info_list) > 0:
            device_info = device_info_list[0]
            model_id = device_info.get("modelId")
            logger.info(f"设备 {device_id} 的 modelId: {model_id}")
            return model_id
        else:
            logger.error(f"无法获取设备 {device_id} 的 modelId")
            return None

    def _batch_address(self, point_list):
        """
        批量获取地址信息
        
        Args:
            point_list: 坐标点列表，如 [{"lat":26.080485,"lon":119.321801,"infoType":3,"modelId":66}]
            
        Returns:
            list: 地址列表，请求失败返回None
        """
        if not self._token:
            logger.info("请先登录获取token")
            return None
            
        url = f"{self._base_url}/api/device/locationManager/batchAddress"
        
        payload = {
            "pointList": point_list
        }
        
        try:
            response = self._session.post(
                url=url,
                json=payload,
                timeout=10
            )
            
            logger.info(f"获取地址状态码: {response.status_code}")
            
            if response.status_code == 200:
                response_data = response.json()
                
                if response_data.get("code") == 1000:  # 操作成功
                    logger.info("获取地址成功！")
                    return response_data.get("data", [])
                else:
                    error_msg = response_data.get("msg", "未知错误")
                    logger.error(f"获取地址失败: {error_msg}")
                    return None
            else:
                logger.error(f"获取地址请求失败，状态码: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取地址请求发生错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取地址发生未知错误: {e}")
            return None

    def get_location(self):
        location = []
        token = self._login()
        if token:
            logger.info(f"获取到的token: {token}")
            device_list = self._get_device_list(size=100, current=1)
            if device_list and "records" in device_list:
                records = device_list["records"]
                if records:
                    logger.info(f"共有 {len(records)} 个设备")
                    
                # 遍历每个设备
                for device in records:
                    device_id = device["id"]
                    device_name = device["name"]
                    latitude = device["latitude"]
                    longitude = device["longitude"]
                    info_type = device["infoType"]
                    
                    logger.info(f"\n处理设备: {device_name} (ID: {device_id})")
                    logger.info(f"位置: 经度 {longitude}, 纬度 {latitude}")
                    
                    # 获取设备详细信息以获取modelId
                    device_info_list = self._get_curr_point_info_all([device_id])
                    if device_info_list:
                        device_info = device_info_list[0]
                        model_id = device_info.get("modelId")
                        logger.info(f"设备型号ID: {model_id}")
                        
                        # 调用批量地址查询接口
                        point_list = [{
                            "lat": latitude,
                            "lon": longitude,
                            "infoType": info_type,
                            "modelId": model_id
                        }]
                        
                        address = self._batch_address(point_list)
                        if address:
                            logger.info(f"详细地址: {address[0]}")
                            bd09_location = {
                                "latitude": latitude,
                                "longitude": longitude,
                            }
                            
                            gcj02 = coord_transfrom.bd09_to_gcj02(longitude, latitude)

                            gcj02_location = {
                                "latitude": gcj02[1],
                                "longitude": gcj02[0],
                            }
                            location.append({
                                "device_id" : device_id,
                                "device_name": device_name,
                                "bd09_location": bd09_location,
                                "gcj02_location": gcj02_location,
                                "info_type": info_type,
                                "model_id": model_id,
                                "address": address
                            })
                        else:
                            logger.error("获取地址失败")
                    else:
                        logger.error("获取设备详细信息失败")
                else:
                    logger.error("设备列表为空")
            else:
                logger.error("获取设备列表失败")
            
        else:
            logger.error("登录失败")
        
        # 使用完毕后关闭会话
        self._session.close()

        return location

    def get_headers(self):
        """获取当前请求头（用于调试）"""
        return dict(self._session.headers)
    
    def close(self):
        """关闭会话"""
        self._session.close()
# 使用示例
if __name__ == "__main__":
    qb = QBLocation()
    
    location = qb.get_location()
    print(location)