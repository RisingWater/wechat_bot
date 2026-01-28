import time
import json
import logging
import threading
from datetime import datetime
from typing import List, Dict, Any
from config import ConfigManager
from webapi.zhixue import ZhixueAPI

router_data = [
    {
        "chatname" : "学霸乔宝专项配套办公室"
    },
    #{
    #    "chatname" : "王旭"
    #},
]

# 设置日志
logger = logging.getLogger(__name__)

class ExamLoop:
    def __init__(self, wxauto_client, env_file: str = ".env"):
        self._env_file = env_file
        self._running = False
        self.wxauto_client = wxauto_client
        self._zhixue = ZhixueAPI()
        self._last_process_time = time.time()
        self._interval = 300
        self._restore_timer = None
    
    def process_loop(self, config_manager):
        """处理所有提醒"""
        current_time = time.time()
        time_since_last = current_time - self._last_process_time
        if time_since_last < self._interval:
            return
        
        # 更新上次执行时间
        self._last_process_time = current_time

        logger.info("开始处理exam_loop 任务")

        try:
            exam_list = self._zhixue.get_exam_list()
            
            for exam in exam_list:
                exam_id = exam.get('examId')
                exam_name = exam.get('examName')
            
                logger.info(f"正在获取考试: {exam_name}")
                report_data = self._zhixue.get_exam_report(exam_id)

                logging.info(report_data)

                for report in report_data:
                    record = config_manager.get_qbexam(report.get("paperId"))
                    notify = False
                    if not record:
                        logger.info(f"发现未记录的考试: {report.get("paperName")}")
                        config_manager.put_qbexam(report)
                        notify = True

                        for route in router_data:
                            chatname = route.get("chatname")
                            if chatname:
                                msg = f"🎉🎉🎉 乔宝 {report.get("paperName")} 成绩出来啦，分数{report.get("userScore")}"
                                if self.wxauto_client:
                                    self.wxauto_client.send_text_message(chatname, msg)
                                else:
                                    logger.info(msg)
                    else:
                        logging.info(f"已记录的考试: {report.get('paperName')}")

                if notify:
                    total_score = 0
                    full_score = 0
                    msg = f"{exam_name}\n"
                    for report in report_data:
                        total_score += report.get("userScore")
                        full_score += report.get("standardScore")
                        msg += f"{report.get("subjectName")}: {report.get("userScore")}\n"
                    msg += f"目前总分：{total_score}"
                    for route in router_data:
                        chatname = route.get("chatname")
                        if chatname:
                            if self.wxauto_client:
                                self.wxauto_client.send_text_message(chatname, msg)
                            else:
                                logger.info(msg)
                       
        except Exception as e:
            logger.error(f"处理提醒时出错: {e}")
    