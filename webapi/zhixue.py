import requests
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ZhixueAPI:
    def __init__(self):
        self._base_url = "https://ali-bg.zhixue.com"
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

    def _get_token(self):
        url = "https://www.zhixue.com/container/app/token/getToken"
    
        # 完整的Cookie（直接从你的请求头复制）
        cookies = {
            "JSESSIONID": "477F73A7BB4A947FDED54B8E4A74E479",
            "aliyungf_tc": "339238218f609287e093238c729f6300cc2b93a8ab90cc123f90b71fd454f22e",
            "tlsysSessionId": "a884bacd-5c18-4965-89e8-8d99abcf9507",
            "isJump": "true",
            "deviceId": "89AFABEE-B805-44FA-96BA-7F4196FA5D04",
            "_bl_uid": "t1mvCk5mx7jct861qvFjpU3d5zbU",
            "loginUserName": "17139721",
            "SSO_R_SESSION_ID": "c6bbdac2-d15c-4315-9af3-b7178d3c0d39",
            "ui": "1500000100282078985",
            "edu_collect_sdk_idxId&devIdBRN44YaIO73": '%7B%22deviceId%22%3A%22900109e4-027a-6e04-97d5-7cbbc490bb98%22%2C%22BRN44YaIO732026-1-28%22%3A14%7D',
            "JSESSIONID": "7947FF034E7E1539D591DFEC0016C997"
        }
        
        try:
            logging.info("正在获取token...")
            
            response = requests.get(
                url=url,
                cookies=cookies,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # 检查常见的成功字段
                    if data.get('errorCode') == 0:
                        logging.info("✅ Token获取成功!")
                        
                        # 提取token信息
                        result_data = data.get('result')
                        
                        return result_data
                    else:
                        logging.error(f"❌ 获取失败: {data.get('errorInfo', '未知错误')}")
                        return None
                        
                except json.JSONDecodeError:
                    logging.error("响应不是JSON格式:")
                    logging.error(response.text[:500])
                    return None
            else:
                logging.error(f"❌ 请求失败，状态码: {response.status_code}")
                logging.error(f"响应内容: {response.text[:500]}")
                return None
                
        except Exception as e:
            logging.error(f"❌ 发生错误: {e}")
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