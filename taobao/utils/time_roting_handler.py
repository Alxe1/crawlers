# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : time_roting_handler.py
# @Software: PyCharm
# Desc     :
import os
import re
import datetime
import logging

try:
    import codecs
except ImportError:
    codecs = None


class MultiprocessHandler(logging.FileHandler):
    """支持多进程的TimedRotatingFileHandler"""
    def __init__(self, filename, when='D', interval=1, backupCount=0, encoding=None, delay=False):
        """filename 日志文件名,when 时间间隔的单位,backupCount 保留文件个数
        delay 是否开启 OutSteam缓存
            True 表示开启缓存，OutStream输出到缓存，待缓存区满后，刷新缓存区，并输出缓存数据到文件。
            False表示不缓存，OutStrea直接输出到文件"""

        self.when = when.upper()
        self.backupCount = backupCount
        # Calculate the real rollover interval, which is just the number of
        # seconds between rollovers.  Also set the filename suffix used when
        # a rollover occurs.  Current 'when' events supported:
        # S - Seconds
        # M - Minutes
        # H - Hours
        # D - Days
        # midnight - roll over at midnight
        # W{0-6} - roll over on a certain day; 0 - Monday
        #
        # Case of the 'when' specifier is not important; lower or upper case
        # will work.
        if self.when == 'S':
            self.interval = 1  # one second
            self.suffix = "%Y-%m-%d_%H-%M-%S"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'M':
            self.interval = 60  # one minute
            self.suffix = "%Y-%m-%d_%H-%M"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}(\.\w+)?$"
        elif self.when == 'H':
            self.interval = 60 * 60  # one hour
            self.suffix = "%Y-%m-%d_%H"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}_\d{2}(\.\w+)?$"
        elif self.when == 'D' or self.when == 'MIDNIGHT':
            self.interval = 60 * 60 * 24  # one day
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        elif self.when.startswith('W'):
            self.interval = 60 * 60 * 24 * 7  # one week
            if len(self.when) != 2:
                raise ValueError("You must specify a day for weekly rollover from 0 to 6 (0 is Monday): %s" % self.when)
            if self.when[1] < '0' or self.when[1] > '6':
                raise ValueError("Invalid day specified for weekly rollover: %s" % self.when)
            self.dayOfWeek = int(self.when[1])
            self.suffix = "%Y-%m-%d"
            self.extMatch = r"^\d{4}-\d{2}-\d{2}(\.\w+)?$"
        else:
            raise ValueError("Invalid rollover interval specified: %s" % self.when)

        self.extMatch = re.compile(self.extMatch, re.ASCII)
        self.interval = self.interval * interval  # multiply by units requested
        self.prefix = filename
        if not self.suffix:
            raise ValueError(u"指定的日期间隔单位无效: %s" % self.when)
        # 拼接文件路径 格式化字符串
        self.filefmt = os.path.join("logs", "%s.%s" % (self.prefix, self.suffix))
        # 使用当前时间，格式化文件格式化字符串
        self.filePath = datetime.datetime.now().strftime(self.filefmt)
        # 获得文件夹路径
        _dir = os.path.dirname(self.filefmt)
        try:
            # 如果日志文件夹不存在，则创建文件夹
            if not os.path.exists(_dir):
                os.makedirs(_dir)
        except Exception:
            pass

        if codecs is None:
            encoding = None

        logging.FileHandler.__init__(self, self.filePath, 'a+', encoding, delay)

    def shouldChangeFileToWrite(self):
        """更改日志写入目的写入文件
        :return True 表示已更改，False 表示未更改"""
        # 以当前时间获得新日志文件路径
        _filePath = datetime.datetime.now().strftime(self.filefmt)
        # 新日志文件日期 不等于 旧日志文件日期，则表示 已经到了日志切分的时候
        #   更换日志写入目的为新日志文件。
        # 例如 按 天 （D）来切分日志
        #   当前新日志日期等于旧日志日期，则表示在同一天内，还不到日志切分的时候
        #   当前新日志日期不等于旧日志日期，则表示不在
        # 同一天内，进行日志切分，将日志内容写入新日志内。
        if _filePath != self.filePath:
            self.filePath = _filePath
            return True
        return False

    def doChangeFile(self):
        """输出信息到日志文件，并删除多于保留个数的所有日志文件"""
        # 日志文件的绝对路径
        self.baseFilename = os.path.abspath(self.filePath)
        # stream == OutStream
        # stream is not None 表示 OutStream中还有未输出完的缓存数据
        if self.stream:
            # flush close 都会刷新缓冲区，flush不会关闭stream，close则关闭stream
            self.stream.flush()
            self.stream.close()  # 测试发现有第一个文件关不掉的现象
            self.stream = None
            # 关闭stream后必须重新设置stream为None，否则会造成对已关闭文件进行IO操作。
        # delay 为False 表示 不OutStream不缓存数据 直接输出
        #   所有，只需要关闭OutStream即可
        if not self.delay:
            # 这个地方如果关闭colse那么就会造成进程往已关闭的文件中写数据，从而造成IO错误
            # delay == False 表示的就是 不缓存直接写入磁盘
            # 我们需要重新在打开一次stream
            self.stream = self._open()
        # 删除多于保留个数的所有日志文件
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                try:
                    os.remove(s)
                except Exception:
                    pass

    def getFilesToDelete(self):
        """获得过期需要删除的日志文件"""
        # 分离出日志文件夹绝对路径
        # split返回一个元组（absFilePath,fileName)
        # 例如：split('C:\Users\Administrator\AppData\logs\log.2008-08-08）
        # 返回（C:\Users\Administrator\AppData\logs， log.2008-08-08）
        dirName, baseName = os.path.split(self.baseFilename)
        fileNames = os.listdir(dirName)
        result = []
        # self.prefix 为日志文件名 列如：log.2008-08-08 中的 log
        # 加上 点号 . 方便获取点号后面的日期
        baseName = baseName.split(".")[0]
        prefix = baseName
        plen = len(prefix)
        for fileName in fileNames:
            if fileName[:plen] == prefix:
                # suffix为日期后缀 log.2008-08-08 中的 2008-08-08
                suffix = fileName[plen+1:]
                # 匹配符合规则的日志文件，添加到result列表中
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirName, fileName))
        # 返回  待删除的日志文件
        # 多于 保留文件个数 backupCount的所有前面的日志文件。
        if len(result) < self.backupCount:
            result = []
        else:
            result.sort()
            result = result[:len(result) - self.backupCount]
        return result

    def emit(self, record):
        """
        发送一个日志记录
        覆盖FileHandler中的emit方法，logging会自动调用此方法
        :param record:
        :return:
        """
        try:
            if self.shouldChangeFileToWrite():
                self.doChangeFile()
            logging.FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
