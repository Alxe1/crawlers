# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : redis_connection.py
# @Software: PyCharm
# @Time    : 2019/7/27 14:53
# Desc     :
import redis


def get_redis():
    return redis.Redis(host='127.0.0.1', port=6379)



if __name__ == "__main__":
    res = redis.Redis(host='127.0.0.1', port=6379)
    res.set("taobao:costume:1", 1)
    res.set("taobao:costume:2", 2)
    res.set("taobao:costume:3", 3)
    res.get("taobao:costume:1")
    print(res.delete("taobao:costume:6"))