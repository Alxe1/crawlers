# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : mongo_connection.py
# @Software: PyCharm
# @Time    : 2019/7/27 14:53
# Desc     :
from pymongo import MongoClient
from pymongo.errors import AutoReconnect
from retrying import retry


def get_mongo():
    return MongoClient(host="127.0.0.1", port=27017)


def retry_if_auto_reconnect_error(exception):
    """Return True if we should retry (in this case when it's an AutoReconnect), False otherwise"""
    return isinstance(exception, AutoReconnect)


@retry(retry_on_exception=retry_if_auto_reconnect_error, stop_max_attempt_number=3, wait_fixed=3000)
def save_to_mongo(collection, value):
    if len(value) != 0:
        try:
            if isinstance(value, list):
                collection.insert_many(value)
            else:
                collection.insert(value)
        except Exception as e:
            print(e)


@retry(retry_on_exception=retry_if_auto_reconnect_error, stop_max_attempt_number=3, wait_fixed=3000)
def update_mongo(collection, condition, value):
    """
    update
    :param collection: 要操作的doc
    :param condition: 更新的查询条件
    :param value: 更新值，字典形式
    :return:
    """
    collection.update_one(condition, {"$set": value})