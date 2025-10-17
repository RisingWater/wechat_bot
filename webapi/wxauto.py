# wxauto.py
import requests
import json
import os
import logging
from env import EnvConfig

logger = logging.getLogger(__name__)

class WXAuto:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._api_url = None
        self._token = None
        self._load_config()
    
    def _load_config(self):
        """Load WXAuto configuration from environment"""
        wxauto_config = self._config.get_wxauto_config()
        self._api_url = wxauto_config.get('api_url')
        self._token = wxauto_config.get('api_key')
        
        if not self._api_url or not self._token:
            logger.warning("WXAuto API URL or Token not found in environment")
        else:
            logger.info("WXAuto configuration loaded successfully")
    
    def send_text_message(self, who, msg, wxname="", exact=False, clear=True, at=""):
        """
        Send text message via WXAuto API
        
        Args:
            who (str): Recipient name (e.g., "文件传输助手")
            msg (str): Message content to send
            wxname (str): WeChat name (optional)
            exact (bool): Whether to match recipient exactly
            clear (bool): Whether to clear input after sending
            at (str): @ someone (optional)
            
        Returns:
            dict: API response
        """
        if not self._api_url or not self._token:
            error_msg = "WXAuto API URL or Token not configured"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            url = f"{self._api_url}/v1/wechat/send"
            
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {self._token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "wxname": wxname,
                "who": who,
                "exact": exact,
                "msg": msg,
                "clear": clear,
                "at": at
            }
            
            logger.info(f"Sending message to '{who}': {msg[:50]}...")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Message sent successfully to '{who}'")
                return {"success": True, "data": result}
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
    def get_next_new_message(self, wxname="", filter_mute=False):
        """
        Get next new message via WXAuto API
        
        Args:
            wxname (str): WeChat name (optional)
            filter_mute (bool): Whether to filter muted chats
            
        Returns:
            dict: API response with message data
        """
        if not self._api_url or not self._token:
            error_msg = "WXAuto API URL or Token not configured"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            url = f"{self._api_url}/v1/wechat/getnextnewmessage"
            
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {self._token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "wxname": wxname,
                "filter_mute": filter_mute
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get("success"):
                    message_data = result.get("data", {})
                    messages = message_data.get("msg", [])
                    
                    if messages:
                        logger.info(f"Received new message from '{message_data.get('chat_name', 'Unknown')}'")
                        return {
                            "success": True,
                            "has_message": True,
                            "chat_name": message_data.get("chat_name"),
                            "chat_type": message_data.get("chat_type"),
                            "messages": messages,
                            "raw_data": result
                        }
                    else:
                        return {
                            "success": True,
                            "has_message": False,
                            "raw_data": result
                        }
                else:
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"API returned error: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "raw_data": result
                    }
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def upload_file(self, file_path, description="", uploader=""):
        """
        Upload file via WXAuto API
        
        Args:
            file_path (str): Path to the file to upload
            description (str): File description (optional)
            uploader (str): Uploader name (optional)
            
        Returns:
            dict: API response with file_id
        """
        if not self._api_url or not self._token:
            error_msg = "WXAuto API URL or Token not configured"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        if not os.path.exists(file_path):
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        try:
            url = f"{self._api_url}/api/v1/files/upload"
            
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {self._token}',
            }
            
            files = {
                'file': (os.path.basename(file_path), open(file_path, 'rb')),
            }
            
            data = {}
            if description:
                data['description'] = description
            if uploader:
                data['uploader'] = uploader
            
            logger.info(f"Uploading file: {file_path}")
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"File uploaded successfully: {result.get('filename')}, file_id: {result.get('file_id')}")
                return {"success": True, "data": result}
            else:
                error_msg = f"File upload failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during file upload: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during file upload: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        finally:
            # Ensure file is closed
            if 'files' in locals():
                files['file'][1].close()

    def send_file_message(self, who, file_path, wxname="", exact=False, description="", uploader=""):
        """
        Send file message via WXAuto API
        
        Args:
            who (str): Recipient name (e.g., "文件传输助手")
            file_path (str): Path to the file to send
            wxname (str): WeChat name (optional)
            exact (bool): Whether to match recipient exactly
            description (str): File description for upload (optional)
            uploader (str): Uploader name for upload (optional)
            
        Returns:
            dict: API response
        """
        if not self._api_url or not self._token:
            error_msg = "WXAuto API URL or Token not configured"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Step 1: Upload file
        upload_result = self.upload_file(file_path, description, uploader)
        if not upload_result.get("success"):
            return upload_result
        
        file_id = upload_result["data"].get("file_id")
        if not file_id:
            error_msg = "No file_id returned from upload"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        
        # Step 2: Send file using file_id
        try:
            url = f"{self._api_url}/v1/wechat/sendfile"
            
            headers = {
                'accept': 'application/json',
                'Authorization': f'Bearer {self._token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "wxname": wxname,
                "who": who,
                "exact": exact,
                "file_id": file_id
            }
            
            logger.info(f"Sending file to '{who}': {os.path.basename(file_path)}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"File sent successfully to '{who}': {os.path.basename(file_path)}")
                    return {"success": True, "data": result, "file_info": upload_result["data"]}
                else:
                    error_msg = result.get("message", "Unknown error in send file")
                    logger.error(f"Send file failed: {error_msg}")
                    return {"success": False, "error": error_msg, "raw_data": result}
            else:
                error_msg = f"Send file API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg, "status_code": response.status_code}
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during file send: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during file send: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

# Test function
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing WXAuto class...")
    
    wxauto = WXAuto()
    
    # Test sending to specific contact
    print("\nTesting send to specific contact...")
    result = wxauto.send_text_message(
        who="文件传输助手",
        msg="这是一条给特定联系人的测试消息",
        exact=True
    )
    print(f"Success: {result['success']}")
    if not result['success']:
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()