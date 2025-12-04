import requests
import logging

logger = logging.getLogger(__name__)

class TencentStockAPI:
    """腾讯股票API"""
    def __init__(self, env_file=".env"):
        return
    def get_stock_price(self, symbol):
        """获取股票当前价格"""
        # 判断市场前缀
        if symbol.startswith('6'):
            prefix = 'sh'
        elif symbol.startswith('0') or symbol.startswith('3'):
            prefix = 'sz'
        else:
            return None

        url = f"http://qt.gtimg.cn/q={prefix}{symbol}"
        try:
            response = requests.get(url, timeout=5)
            data = response.text.split('~')
            # 当前价格是第3个字段（索引为3）
            current_price = float(data[3])
            stock_name = data[1]  # 股票名称
            return {
                'name': stock_name,
                'symbol': symbol,
                'price': current_price
            }
        except Exception as e:
            return None

    def get_stock_code(self, stock_name):
        """根据股票名称获取6位数字代码"""
        url = "https://smartbox.gtimg.cn/s3/"
        params = {"v": "2", "q": name, "t": "all"}
        
        try:
            resp = requests.get(url, params=params, timeout=3)
            if resp.status_code != 200:
                return None
                
            # 解析JSONP
            text = resp.text
            start = text.find("_(") + 2
            end = text.rfind(")")
            data = json.loads(text[start:end])
            
            # 提取第一个A股代码
            for item in data[0].get("item", []):
                code = item.get("c", "")
                if code.startswith(("sh", "sz")) and len(code) == 8:
                    return code[2:]  # 返回6位数字代码
            
            return None
        except:
            return None

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    tencent_api = TencentStockAPI()
    logger.info("腾讯股票API测试")
    logger.info(tencent_api.get_stock_price("sz002396"))
    logger.info(tencent_api.get_stock_price("sz000063"))
    logger.info(tencent_api.get_stock_price("sh603828"))
