import requests

class TencentStockAPI:
    """腾讯股票API"""
    def __init__(self, env_file=".env"):
        return
    def get_stock_price(self, symbol):
        """获取股票当前价格"""
        url = f"http://qt.gtimg.cn/q={symbol}"
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
            return f"获取价格失败: {e}"

def main():
    tencent_api = TencentStockAPI()
    print("腾讯股票API测试")
    print(tencent_api.get_stock_price("sz002396"))
    print(tencent_api.get_stock_price("sz000063"))
    print(tencent_api.get_stock_price("sh603828"))

if __name__ == "__main__":
    main()
