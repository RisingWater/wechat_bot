# homework.py
import logging
import os
import base64
import requests
import re
import tempfile
import random
from datetime import datetime, timedelta
from webapi.tencent_stock import TencentStockAPI
from webapi.deepseek import DeepSeekAPI
from utils.stock_tools import StockTools

logger = logging.getLogger(__name__)

class StockProcessor:
    def __init__(self, env_file=".env"):
        self._deepseek = DeepSeekAPI(env_file)
        self.processor_name = "urlsave_processor"
        logger.info(f"UrlSaveProcessor initialized")
    
    def description(self) -> str:
        return "股票预测处理器"  
    
    def priority(self) -> int:
        return 20
    
    def _get_predict_date(self):
        """
        确定预测日期
        规则：15:00-24:00 预测明天，0:00-9:00 预测今天，其他时间也预测今天
        """
        now = datetime.now()
        current_hour = now.hour
        
        if (StockTools().is_trading_day(now.strptime(now, '%Y-%m-%d'))) :
            if current_hour >= 9 and current_hour < 17:
                # 9:00-17:00 预测今天
                predict_date = StockTools().get_trading_day(now, delta=0)
            else:
                # 17:00-24:00 预测明天
                predict_date = StockTools().get_trading_day(now, delta=1)
        else:
            predict_date = StockTools().get_trading_day(now, delta=1)
        
        return predict_date
    
    def _send_explain(self, wxauto_client, chat_name, stock_name, predict_date, predictions):
        try:
            prompt = f"你是一个精通中国传统文化、易经八卦、阴阳五行理论的股票分析师，擅长将现代金融市场数据与古典玄学相结合，提供独特的分析。"
            prompt += f"现在要求解释股票{stock_name}，预测{predict_date}的k线为{predictions}"
            prompt += f"以股票名称的五行属性，卦象，结合预测日期进行解释，以一个算命师的口吻来解释预测结果，不超过100字，结果中必须要带有股票名称。不要输出其它额外的内容。"

            response = self._deepseek.ask_question(prompt)
            
            if response:
                response = response.strip()
                logger.info(f"DeepSeek explain: '{response}'")
                wxauto_client.send_text_message(who=chat_name, msg=response)
            else:
                logger.error("DeepSeek API returned no explain")
                return
                
        except Exception as e:
            logger.error(f"Error in explain: {str(e)}")
            return
    
    def _get_internet_slang_msg(self, stock_name, stock_code, predict_date):
        messages = [
            f"等一下，{stock_name}是吧，算一下先",
            f"{stock_name}，算ing",
            f"{stock_name}开整，等会儿",
            f"等等，我掐指一算{stock_name}",
            f"{stock_name}天机不可泄漏，稍安勿躁",
            f"正在做法，{stock_name} 请稍等",
            f"{stock_name}，算好了告诉你",
            f"这是啥？{stock_name}？，有点意思，我算算",
            f"{stock_name}？，等等我看看",
            f"又来？{stock_name}，搞起",
            f"天有不测风云，人有旦夕祸福{stock_name}，到底如何，让我掐指一算",
            f"微信真垃圾，发个消息都这么麻烦，{stock_name}，是吧，稍等",
            f"我靠手机好像卡了，你问{stock_name}对吧，等等我",
            f"兄弟，别急，{stock_name}，我这就给你算",
            f"哎呀，{stock_name}，让我先喝口茶，马上给你答案",
            f"你这问题有点意思，{stock_name}，让我想想",
            f"{stock_name}？好问题，让我掐指一算",
            f"算命先生我来了，{stock_name}，等我一会儿",
            f"先别急，{stock_name}，让我掐指一算",
            f"{stock_name}？让我先翻翻黄历",
            f"这个问题有点复杂，{stock_name}，让我想想",
            f"算命可不是儿戏，{stock_name}，稍等片刻",
            f"天地玄黄，宇宙洪荒，我给你算一个{stock_name}",
            f"算命不是预测，{stock_name}，不一定准的",
            f"微信张小龙大司马命我来算，{stock_name}，稍安勿躁",
            f"今天天气不错，适合算命，{stock_name}，等我一会儿",
        ]
        
        # 选择一条基础消息
        base_msg = random.choice(messages)
        
        # 微信表情包列表（精选与算命/计算相关的）
        emojis = [
            # 思考/等待相关
            "🤔", "🤨", "🧐", "😏", "😌",
            # 日常/幽默相关
            "😅", "😂", "🤣", "😉", "😎", "🤓", "😜", "🤪", "😝", "🤗",
            # 动作/操作相关
            "🙏", "🤏", "👌", "🤙", "✌️", "🤞", "👐", "🙌", "👏", "🤲", "🙏",
        ]
        
        # 随机决定是否添加表情
        if random.random() < 0.5:
            num_emojis = random.randint(1, 2)
            selected_emojis = random.sample(emojis, num_emojis)
            
            # 随机位置：开头、结尾、中间、或环绕
            position = random.choices(
                ["start", "end", "both"],
                weights=[0.4, 0.4, 0.2],  # 权重调整
                k=1
            )[0]
            
            if position == "start":
                # 在开头添加表情
                return f"{''.join(selected_emojis)} {base_msg}"
            elif position == "end":
                # 在结尾添加表情
                return f"{base_msg} {''.join(selected_emojis)}"
            elif position == "both":
                # 在开头和结尾都添加
                half = len(selected_emojis) // 2
                return f"{''.join(selected_emojis[:half])} {base_msg} {''.join(selected_emojis[half:])}"
        
        # 10%的概率不加表情，保持原样
        return base_msg

    def process_text(self, text_msg, wxauto_client):
        """
        处理文本消息
        
        Args:
            text_msg (dict): 文本消息数据
            wxauto_client: wxauto客户端实例
            
        Returns:
            bool: 处理成功返回True，失败返回False
        """
        try:
            chat_name = text_msg.get("chat_name")
            text_content = text_msg.get("text_content")
            chat_type = text_msg.get("chat_type")
            
            if chat_type == "group":
                if not "@呼噜一号" in text_content:
                    logger.info(f"text message from {chat_name}, not @bot skipping")
                    return False
                #去掉 @呼噜一号，再去除头尾的空格
                text_content = text_content.replace("@呼噜一号", "")
                text_content = text_content.replace(" ", "")
                text_content = text_content.strip()


            # 检查text_content是否为6位数字
            if re.match(r'^\d{6}$', str(text_content)):
                stock_code = text_content
            
                # 获取股票名称
                stock_dict = TencentStockAPI().get_stock_price(stock_code)
                if not stock_dict:
                    error_msg = f"未找到股票代码 '{stock_code}' 对应的股票名称"
                    self._send_error_response(wxauto_client, chat_name, error_msg)
                    return True
                
                stock_name = stock_dict.get("name")
            else:
                stock_code = TencentStockAPI().get_stock_code(text_content)
                if not stock_code:
                    #error_msg = f"未找到股票名称 '{text_content}' 对应的股票代码"
                    #self._send_error_response(wxauto_client, chat_name, error_msg)
                    logger.warning(f"未找到股票名称 '{text_content}' 对应的股票代码")
                    return False
                stock_name = text_content

            # 确定预测日期
            predict_date = self._get_predict_date()

            # 使用示例
            msg = self._get_internet_slang_msg(stock_name, stock_code, predict_date)
            wxauto_client.send_text_message(who=chat_name, msg=msg)
            
            # 构建预测请求
            predict_data = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "predict_type": "daily",
                "predict_date": predict_date,
                "predict_len": 1
            }

            # 调用预测API
            try:
                response = requests.post(
                    "http://192.168.1.180:6029/predict",
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    json=predict_data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    error_msg = f"预测API调用失败，状态码：{response.status_code}"
                    self._send_error_response(wxauto_client, chat_name, error_msg)
                    return True
                
                result = response.json()
                
                # 检查返回结果
                if "predictions" not in result or not result["predictions"]:
                    error_msg = "预测API返回数据格式异常"
                    logger.error(f"预测API返回数据格式异常 response: {response.json()}")
                    self._send_error_response(wxauto_client, chat_name, error_msg)
                    return True
                
                # 处理预测结果
                chart_image = result.get("chart_image", "")

                predictions = result.get("predictions")
                                
                # 如果有图表图片，发送图片
                if chart_image:
                    self._send_chart_image(wxauto_client, chat_name, chart_image)

                if chat_type == "group" and predictions:
                    self._send_explain(wxauto_client, chat_name, stock_name, predict_date, predictions)
                
                return True
                
            except requests.exceptions.Timeout:
                error_msg = "预测API请求超时，请稍后重试"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return True
            except requests.exceptions.ConnectionError:
                error_msg = "无法连接到预测API服务器"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return True
            except Exception as e:
                error_msg = f"预测API调用异常：{str(e)}"
                self._send_error_response(wxauto_client, chat_name, error_msg)
                return True

        except Exception as e:
            logger.error(f"Error processing chat text: {str(e)}")
            return True
       
    def _send_chart_image(self, wxauto_client, chat_name, chart_image_base64):
        """
        发送图表图片 - 使用tempfile确保文件清理
        """
        if not chart_image_base64 or not wxauto_client or not chat_name:
            return False
        
        temp_file = None
        try:
            # 解码base64图片
            image_data = base64.b64decode(chart_image_base64)
            
            # 创建临时文件 - 自动清理
            with tempfile.NamedTemporaryFile(
                suffix='.png', 
                prefix='stock_chart_',
                delete=False  # 先不自动删除，等发送完再删
            ) as temp_file:
                # 写入图片数据
                temp_file.write(image_data)
                temp_file.flush()  # 确保数据写入磁盘
                temp_file_path = temp_file.name
            
            # 发送图片文件
            send_result = wxauto_client.send_file_message(
                who=chat_name,
                file_path=temp_file_path,
                exact=True,
                description="股票价格预测图表",
                uploader="stock_processor"
            )
            
            return send_result
            
        except Exception as e:
            logger.error(f"发送图表图片失败：{str(e)}")
            return False
        
        finally:
            # 无论成功失败，都清理临时文件
            if temp_file and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)  # 删除临时文件
                except Exception as e:
                    logger.error(f"清理临时文件失败：{str(e)}")

    def _send_error_response(self, wxauto_client, chat_name, error_message):
        """
        发送错误响应
        
        Args:
            wxauto_client: wxauto客户端实例
            chat_name (str): 聊天名称
            error_message (str): 错误消息
        """
        if wxauto_client and chat_name:
            try:
                wxauto_client.send_text_message(who=chat_name, msg=error_message)
            except Exception as e:
                logger.error(f"Failed to send error response: {str(e)}")
  