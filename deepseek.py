# deepseek.py
import requests
import json
import logging
from env import EnvConfig

logger = logging.getLogger(__name__)

class DeepSeekAPI:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._api_key = None
        self._load_config()
    
    def _load_config(self):
        """Load DeepSeek configuration from environment"""
        deepseek_config = self._config.get_deepseek_config()
        self._api_key = deepseek_config.get('api_key')
        
        if not self._api_key:
            logger.warning("DeepSeek API key not found in environment")
        else:
            logger.info("DeepSeek configuration loaded successfully")
    
    def ask_question(self, prompt, model="deepseek-chat", timeout=60):
        """
        Send question to DeepSeek API and get response
        
        Args:
            prompt (str): The question or prompt to send
            model (str): Model to use
            timeout (int): Request timeout in seconds
            
        Returns:
            str: API response content, or None if failed
        """
        if not self._api_key:
            error_msg = "DeepSeek API key not configured"
            logger.error(error_msg)
            return None
        
        try:
            url = "https://api.deepseek.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}"
            }
            
            data = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False
            }
            
            logger.info("Sending request to DeepSeek API...")
            
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                logger.info("DeepSeek API request successful")
                return content
            else:
                logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error calling DeepSeek API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error calling DeepSeek API: {str(e)}")
            return None
    
# Test function
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing DeepSeek API...")
    
    deepseek = DeepSeekAPI()
        
    # Test with a simple question
    test_prompt = "请用一句话介绍你自己"
    print(f"\nTesting with prompt: {test_prompt}")
    
    response = deepseek.ask_question(test_prompt)
    if response:
        print(f"Response: {response}")
    else:
        print("Failed to get response from DeepSeek API")

if __name__ == "__main__":
    main()