import requests
import time
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ZhixueAPI:
    def __init__(self):
        self._base_url = "https://ali-bg.zhixue.com"

        self._deviceId = "e640163b58dd034bd6872f7df7d60175"
        self._tgt = "TGT-144825-mw0IcWffVT2utvm9YtMkgsaEWtHHzCAACbHwXgk04bfS1ObvHe-open.changyan.com"

        self._token = self._get_token()
        curyear = datetime.now()
        current_year = curyear.year
        current_month = curyear.month
        
        # 判断当前时间属于哪个学年
        # 学年规则：8月1日 - 次年7月31日
        if current_month >= 8:
            # 如果是8月-12月，属于 当前年-次年 学年
            start_year = current_year
            end_year = current_year + 1
        else:
            # 如果是1月-7月，属于 前一年-当前年 学年
            start_year = current_year - 1
            end_year = current_year

        # 计算具体日期
        start_date = datetime(start_year, 8, 1, 0, 0, 0)  # 8月1日 00:00:00
        end_date = datetime(end_year, 7, 31, 23, 59, 59)  # 7月31日 23:59:59
        
        # 转换为毫秒时间戳
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)            

        self._startSchoolYear = start_timestamp
        self._endSchoolYear = end_timestamp


    def _get_at_token(self):
        # 请求URL
        url = "https://open.changyan.com/sso/v1/api"

        # 请求头
        headers = {
            "User-Agent": "zhixue_student/1.0.2047 (iPhone; iOS 26.2.1; Scale/3.00)",
        }

        # 请求体参数（URL编码格式）
        data = {
            "appId": "zhixue_student",
            "client": "ios",
            "deviceId": self._deviceId,
            "deviceName": "iPhone18,3",
            "extInfo": f'{{"deviceId":"{self._deviceId}"}}',
            "method": "sso.extend.tgt",
            "ncetAppId": "SDZSH23Z6LPnq8iCweQrUo5ACJXtKCvG",
            "networkState": "wifi",
            "osType": "ios",
            "tgt": self._tgt,
            "userProxy": "true"
        }

        # 发送POST请求
        try:
            response = requests.post(url, headers=headers, data=data)
            
            # 输出响应信息
            logging.info(f"状态码: {response.status_code}")
            response_json = response.json()

            if response_json.get("code") == "success" :
                return response_json.get("data")
            else:
                logging.error(f"获取AT失败: {response_json.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"请求出错: {e}")
            return None

    def _get_token(self):
        """
        智学网CAS登录函数
        """

        at_response = self._get_at_token()
        if at_response is None:
            logging.error("获取AT失败，请检查网络或重新运行程序")
            return None
        
        at_token = at_response.get("at")
        user_id = at_response.get("userId")
        
        url = "https://www.zhixue.com/container/app/login/casLogin"
        
        # 生成时间戳
        timestamp = str(int(time.time() * 1000))
        
        
        headers = {
            "Host": "www.zhixue.com",
            "sucOriginAppKey": "zhixue_student",
            "User-Agent": "zhixue_student/1.0.2047 (iPhone; iOS 26.2.1; Scale/3.00)",
            "deviceType": "iPhone18,3",
            "deviceName": "iPhone",
            "browserVersion": "iOS_1.0.2047",
            "deviceId": self._deviceId,
            "appName": "com.zhixue.student",
            "sucAccessDeviceId": self._deviceId,
        }
        
        # 请求体参数
        data = {
            "appId": "zhixue_student",
            "at": at_token,
            "ncetAppId": "SDZSH23Z6LPnq8iCweQrUo5ACJXtKCvG",
            "tokenTimeout": "0",
            "userId": user_id
        }
        
        try:
            response = requests.post(url, headers=headers, data=data)
            
            # 输出响应信息
            logging.info(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    # 检查是否成功
                    if result.get("success") and result.get("errorCode") == 0:
                        logging.info("登录成功!")
                        # 提取重要信息
                        user_info = result.get("result", {}).get("userInfo", {})
                        token = result.get("result", {}).get("token", "")
                        
                        logging.info(f"用户姓名: {user_info.get('name')}")
                        logging.info(f"用户ID: {user_info.get('id')}")
                        logging.info(f"班级: {result.get('result', {}).get('clazzInfo', {}).get('name')}")
                        logging.info(f"学校: {user_info.get('school', {}).get('schoolName')}")
                        logging.info(f"Token: {token[:50]}...")  # 只显示前50个字符
                        
                        return token
                    else:
                        logging.error(f"登录失败: {result.get('errorInfo')}")
                except json.JSONDecodeError:
                    logging.error("响应不是有效的JSON格式")
                    logging.error(response.text)
            else:
                logging.error(f"HTTP请求失败: {response.status_code}")
                logging.error(response.text)
                
        except requests.exceptions.RequestException as e:
            logging.error(f"请求出错: {e}")
            return None
        
    def get_exam_list(self):
        url = f"{self._base_url}/zhixuebao/report/exam/getUserExamList"
        
        # 查询参数
        params = {
            "pageIndex": 1,
            "pageSize": 10,
            "startSchoolYear": self._startSchoolYear,
            "endSchoolYear": self._endSchoolYear
        }
        
        # 请求头
        headers = {
            "XToken": self._token,
            "token": self._token
        }
        
        try:
            # 发送GET请求
            response = requests.get(
                url=url,
                params=params,
                headers=headers,
                timeout=10  # 设置超时时间
            )
                    
            # 尝试解析JSON响应
            if response.status_code == 200:
                data = response.json()
                
                if data.get('errorCode') == 0:
                    exam_list = data['result']['examList']
                    
                    # 提取所需信息
                    exams_info = []
                    for exam in exam_list:
                        exams_info.append({
                            'examId': exam['examId'],
                            'examName': exam['examName'],
                            'examType': exam['examType']
                        })
                    
                    return exams_info
                else:
                    logging.error(f"API返回错误: {data.get('errorInfo')}")
                    return None
            else:
                logging.error(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"发生错误: {e}")
            return None
        
    def get_exam_report(self, exam_id):
        """根据examId获取考试报告"""
        url = f"{self._base_url}/zhixuebao/report/exam/getReportMain"
        
        params = {
            "examId": exam_id
        }
        
        # 请求头
        headers = {
            "XToken": self._token,
            "token": self._token
        }
        
        try:
            response = requests.get(
                url=url,
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('errorCode') == 0:
                    paperList = data['result']['paperList']
                    
                    # 提取所需信息
                    paperinfo = []
                    for paper in paperList:
                        paperinfo.append({
                            'paperId': paper['paperId'],
                            'examId' : exam_id,
                            'paperName': paper['paperName'],
                            'subjectName': paper['subjectName'],
                            'userScore': paper['userScore'],
                            'standardScore': paper['standardScore']
                        })
                    
                    return paperinfo
                else:
                    logging.error(f"API返回错误: {data.get('errorInfo')}")
                    return None
            else:
                logging.error(f"请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"获取考试报告时出错: {e}")
            return None
            
# 发送请求
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    zhixue = ZhixueAPI()

    exam_list = zhixue.get_exam_list()

    if exam_list:
        for exam in exam_list:
            exam_id = exam.get('examId')
            exam_name = exam.get('examName')
            
            logging.info(f"正在获取考试: {exam_name}")

            report_data = zhixue.get_exam_report(exam_id)
            if report_data:
                logging.info(report_data)