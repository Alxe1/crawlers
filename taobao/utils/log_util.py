# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : log_util.py
# @Software: PyCharm
# Desc     :
import logging  # 引入logging模块
import logging.handlers
import functools
import com.chargerlink.time_roting_handler as time_roting_handler


def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Log等级总开关
    if not logger.handlers:
        log_path = r"/mam/Logs/P6_plug-in"  # 240服务器日志路径
        logfile = log_path
        # 按照日期做日志分割
        # TODO 目前日志切分没有实现，需要后续调试。
        sh = time_roting_handler.MultiprocessHandler(logfile, when='D', interval=1, backupCount=90, encoding='utf-8')
        sh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
        sh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(sh)
        logger.addHandler(ch)
    return logger


def log_exception(fn):
    """
    这个注解可以将异常打入日志
    支持注解形式
    :param fn:
    :return:
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.exception("[Error in {}] msg: {}".format(__name__, str(e)))
            raise
    return wrapper


if __name__ == '__main__':
    logger = get_logger()