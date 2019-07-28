# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : get_similars.py
# @Software: PyCharm
# @Time    : 2019/7/27 14:17
# Desc     :

import os
import random
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from taobao.costume.crawler.get_details_url import swipe_down, login, get_page
from taobao.utils.mongo_connection import save_to_mongo, get_mongo
from taobao.utils.log_util import get_logger

logger = get_logger()

mongo_client = get_mongo()
crawler_db = mongo_client.crawler_db
collection = crawler_db.taobao_costume_similars


def get_similar_goods_details(driver, page_source):
    similars_price = []
    similars_paid = []

    wait = WebDriverWait(driver, 10)
    soup = BeautifulSoup(page_source, "lxml")

    similars = soup.find_all("div", class_="similars")
    similar_urls = [url.a.get("href") for url in similars]

    for similar_url in similar_urls:
        js = 'window.open("{}");'.format("https://s.taobao.com" + similar_url)
        driver.execute_script(js)
        # 跳转到相似商品页面
        handles = driver.window_handles
        logger.info(handles)
        driver.switch_to.window(handles[1])

        for i in range(100):
            logger.info("第{}页".format(i+1))
            swipe_down(driver, 2)
            try:
                if EC.element_to_be_clickable((By.LINK_TEXT, "下一页")):
                    wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "下一页"))).click()
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, "lxml")
                    prices = [price.text[1:] for price in soup.find_all("div", class_="info2__price")]
                    logger.info(prices)
                    n_paid = [paid.text.strip()[:-3] for paid in soup.find_all("div", class_="info3__npaid")]
                    logger.info(n_paid)
                    similars_price.extend(prices)
                    similars_paid.extend(n_paid)
                    time.sleep(1)
            except TimeoutException:
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, "lxml")
                prices = [price.text[1:] for price in soup.find_all("div", class_="info2__price")]
                logger.info(prices)
                n_paid = [paid.text.strip()[:-3] for paid in soup.find_all("div", class_="info3__npaid")]
                logger.info(n_paid)
                similars_price.extend(prices)
                similars_paid.extend(n_paid)
                time.sleep(1)
                break
            except Exception as e:
                logger.info(e, "没有获取到相同商品信息")
                break

        save_to_mongo(collection,
                      {"similar_prices": similars_price,
                       "similar_paids": similars_paid,
                       "similar_urls": "https://s.taobao.com" + similar_url})

        driver.close()
        driver.switch_to.window(handles[0])


def main(url="https://www.taobao.com", keys="表演服"):
    start_time = time.time()
    logger.info("开始数据爬取")
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
    for page in range(1, 100 + 1):
        if page >= 2:
            get_page(driver, page)
            sleep = random.uniform(10, 20)
            time.sleep(sleep)  # 翻页后睡眠时间
        logger.info("正在获取第{}页的商品信息".format(page))
        # 3. 滑动滚动条
        swipe_down(driver, 2)
        time.sleep(1)
        # 4. 读取源代码
        page_source = driver.page_source
        get_similar_goods_details(driver, page_source)
    logger.info("数据爬取结束，用时：{}".format(time.time() - start_time))

if __name__ == "__main__":
    main()
