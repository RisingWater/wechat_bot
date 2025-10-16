# baidu_ocr.py
import base64
import urllib.parse
import requests
import json
import logging
from env import EnvConfig

logger = logging.getLogger(__name__)

class BaiduOCR:
    def __init__(self, env_file=".env"):
        self._config = EnvConfig(env_file)
        self._bearer_token = None
        self._load_config()
    
    def _load_config(self):
        """Load Baidu OCR configuration"""
        baidu_config = self._config.get_baidu_ocr_config()
        self._bearer_token = baidu_config['api_key']
        
        if not self._bearer_token :
            logger.warning("Baidu OCR API key not found in environment")
    
    def _get_file_content_as_base64(self, path, urlencoded=False):
        """
        Get file base64 encoding
        :param path: file path
        :param urlencoded: whether to urlencode the result
        :return: base64 encoded content
        """
        with open(path, "rb") as f:
            content = base64.b64encode(f.read()).decode("utf8")
            if urlencoded:
                content = urllib.parse.quote_plus(content)
        return content
    
    def _process_image(self, image_path, detect_direction=False, probability=False, detect_alteration=False):
        """
        Process single image file with Baidu OCR API using Bearer token
        """
        try:
            logger.info(f"Processing image: {image_path}")
            
            # Get image as base64
            image_base64 = self._get_file_content_as_base64(image_path, False)
            
            # Prepare request
            url = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting"
            
            # Build payload
            payload_parts = [
                f'image={urllib.parse.quote_plus(image_base64)}',
                f'detect_direction={str(detect_direction).lower()}',
                f'probability={str(probability).lower()}',
                f'detect_alteration={str(detect_alteration).lower()}'
            ]
            payload = '&'.join(payload_parts)
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self._bearer_token}'
            }
            
            # Make request
            response = requests.request("POST", url, headers=headers, data=payload.encode("utf-8"))
            
            if response.status_code == 200:
                result_data = response.json()

                logger.info(result_data)
                
                # Check if OCR was successful
                if 'words_result' in result_data:
                    formatted_results = []
                    for item in result_data['words_result']:
                        formatted_results.append({
                            'text': item.get('words', ''),
                            'confidence': 1.0,
                            'text_region': []
                        })
                    
                    return {
                        "success": True,
                        "results": formatted_results,
                        "raw_result": result_data
                    }
                elif 'error_code' in result_data:
                    return {
                        "success": False,
                        "error": f"Baidu API error: {result_data.get('error_msg', 'Unknown error')}",
                        "raw_result": result_data
                    }
                else:
                    return {
                        "success": False,
                        "error": "No OCR results found",
                        "raw_result": result_data
                    }
            else:
                logger.error(f"Baidu OCR API request failed: {response.status_code} - {response.text}")
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}",
                    "raw_result": response.text
                }
                
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _fake_process_image(self, image_path, detect_direction=False, probability=False, detect_alteration=False):
        """
        Return fake successful OCR response for testing without API calls
        """
        logger.info(f"Using fake OCR response for: {image_path}")
        
        fake_response = {
            'success': True, 
            'results': [
                {'text': 'No.', 'confidence': 1.0, 'text_region': []}, 
                {'text': 'Date', 'confidence': 1.0, 'text_region': []}, 
                {'text': '九月二十八日', 'confidence': 1.0, 'text_region': []}, 
                {'text': '语文:', 'confidence': 1.0, 'text_region': []}, 
                {'text': 'P1-1', 'confidence': 1.0, 'text_region': []}, 
                {'text': '1.阳光课堂练习P51:7.8.9.10题', 'confidence': 1.0, 'text_region': []}, 
                {'text': '2.摘抄(下周1交).', 'confidence': 1.0, 'text_region': []}, 
                {'text': '3.准备小测', 'confidence': 1.0, 'text_region': []}, 
                {'text': '数学:', 'confidence': 1.0, 'text_region': []}, 
                {'text': '1.卷子P53-54.', 'confidence': 1.0, 'text_region': []}, 
                {'text': '英语:', 'confidence': 1.0, 'text_region': []}, 
                {'text': 'yu', 'confidence': 1.0, 'text_region': []}, 
                {'text': '1.准备小测', 'confidence': 1.0, 'text_region': []}, 
                {'text': '2.智学网打卡', 'confidence': 1.0, 'text_region': []}, 
                {'text': '物理;', 'confidence': 1.0, 'text_region': []}, 
                {'text': '1:同步练习P15-16.', 'confidence': 1.0, 'text_region': []}, 
                {'text': '地理.', 'confidence': 1.0, 'text_region': []}, 
                {'text': '1.填充图册P1819.20.21.', 'confidence': 1.0, 'text_region': []}
            ], 
            'raw_result': {
                'words_result': [
                    {'location': {'top': 150, 'left': 97, 'width': 50, 'height': 26}, 'words': 'No.'}, 
                    {'location': {'top': 209, 'left': 99, 'width': 71, 'height': 28}, 'words': 'Date'}, 
                    {'location': {'top': 420, 'left': 83, 'width': 205, 'height': 58}, 'words': '九月二十八日'}, 
                    {'location': {'top': 494, 'left': 90, 'width': 116, 'height': 56}, 'words': '语文:'}, 
                    {'location': {'top': 486, 'left': 903, 'width': 175, 'height': 69}, 'words': 'P1-1'}, 
                    {'location': {'top': 528, 'left': 90, 'width': 618, 'height': 108}, 'words': '1.阳光课堂练习P51:7.8.9.10题'}, 
                    {'location': {'top': 634, 'left': 83, 'width': 298, 'height': 64}, 'words': '2.摘抄(下周1交).'}, 
                    {'location': {'top': 695, 'left': 85, 'width': 389, 'height': 79}, 'words': '3.准备小测'}, 
                    {'location': {'top': 782, 'left': 95, 'width': 121, 'height': 58}, 'words': '数学:'}, 
                    {'location': {'top': 861, 'left': 94, 'width': 239, 'height': 57}, 'words': '1.卷子P53-54.'}, 
                    {'location': {'top': 929, 'left': 88, 'width': 113, 'height': 61}, 'words': '英语:'}, 
                    {'location': {'top': 896, 'left': 938, 'width': 107, 'height': 69}, 'words': 'yu'}, 
                    {'location': {'top': 1000, 'left': 93, 'width': 204, 'height': 68}, 'words': '1.准备小测'}, 
                    {'location': {'top': 1082, 'left': 92, 'width': 247, 'height': 66}, 'words': '2.智学网打卡'}, 
                    {'location': {'top': 1160, 'left': 95, 'width': 133, 'height': 62}, 'words': '物理;'}, 
                    {'location': {'top': 1237, 'left': 93, 'width': 319, 'height': 66}, 'words': '1:同步练习P15-16.'}, 
                    {'location': {'top': 1323, 'left': 90, 'width': 113, 'height': 64}, 'words': '地理.'}, 
                    {'location': {'top': 1406, 'left': 89, 'width': 464, 'height': 67}, 'words': '1.填充图册P1819.20.21.'}
                ], 
                'words_result_num': 18, 
                'log_id': 1978078424916235969
            }
        }
        
        return fake_response

    def recognize_handwriting(self, image_path, **kwargs):
        """
        Main method for handwriting recognition
        """
        return self._process_image(image_path, **kwargs)
        #return self._fake_process_image(image_path, **kwargs)


# Test function
def main():
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Baidu OCR with Bearer token...")
    
    ocr = BaiduOCR()
    
    # Test with sample image if available
    import os
    test_image = "test/baidu_ocr_test.jpg";
    if os.path.exists(test_image):
        print(f"\nTesting OCR with {test_image}...")
        result = ocr.recognize_handwriting(test_image)
        print(f"Success: {result['success']}")
    
        if result['success']:
            print(result)
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
    else:
        print(f"Error: {test_image} is not exist")

if __name__ == "__main__":
    main()    