# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : costume_crawler.py
# @Software: PyCharm
# Desc     :
import re
import time
import random

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from taobao.costume.crawler.get_details_url import login, get_page, swipe_down, get_details
from taobao.utils.mongo_connection import get_mongo, save_to_mongo
from taobao.utils.redis_connection import get_redis


mongo_client = get_mongo()
crawler_db = mongo_client.crawler_db
collection = crawler_db.taobao_costume_details

res = get_redis()
redis_name = "taobao:costume:"


def crawler(url="http:www.taobao.com", keys="表演服"):
    start_time = time.time()
    print("数据爬取开始")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)

    #  登录
    login(driver, url)
    # 寻找输入框
    input = driver.find_element_by_id("q")
    # 1. 搜索关键字
    input.send_keys(keys)
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="J_TSearchForm"]/div[1]/button').click()
    # 2. 销量从高到低
    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='J_relative']/div[1]/div/ul/li[2]/a").click()
    time.sleep(5)
    for page in range(1, 100+1):
        if page >= 2:
            get_page(driver, page)
            sleep = random.uniform(10, 20)
            time.sleep(sleep)  # 翻页后睡眠时间
        print("正在获取第{}页的商品信息".format(page))
        # 3. 滑动滚动条
        time.sleep(2)
        swipe_down(driver, 2)
        # 4. 读取源代码
        page_source = driver.page_source
        goods_infos = get_details(page_source=page_source)
        for goods_info in goods_infos:
            save_to_mongo(collection, goods_info)
            res.set(redis_name+goods_info["goods_name"], 1)
    print("数据爬取结束：{}".format(time.time() - start_time))


def get_goods_comments(driver):
    """
    获取商品的评论信息
    :param driver:
    :return:
    """
    comments_list = []
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "J_Itemlist_TLink_565847562523"))).click()  # TODO:优化
    time.sleep(2)
    # 跳转页面
    handles = driver.window_handles
    driver.switch_to.window(handles[1])
    # 滑动滚动条
    swipe_down(driver, 2)
    # 点击累计评价
    wait.until(EC.presence_of_element_located((By.ID, "J_TabBarBox"))).click()
    while True: # TODO：待测
        time.sleep(5)
        if wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "下一页"))):
            # 解析网页，获得评论
            soup = BeautifulSoup(driver.page_source, "lxml")
            page_source = str(soup.find("div", id="mainwrap"))  # TODO: 进一步优化
            text_list = re.findall("[\u4e00-\u9fa5，。！？]+", page_source)
            comments = [text for text in text_list if len(text) >= 20]
            comments_list.extend(comments)
            wait.until(EC.presence_of_element_located((By.LINK_TEXT, "下一页"))).click()
            swipe_down(driver, 2)
        else:
            break

    return comments_list


if __name__ == "__main__":
    crawler()
