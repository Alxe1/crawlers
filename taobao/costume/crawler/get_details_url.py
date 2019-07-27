# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : get_details_url.py
# @Software: PyCharm
# Desc     :
import json
import os
import re
import time
from itertools import zip_longest
from bs4 import BeautifulSoup
from urllib import request
from selenium import webdriver


def login(driver, url, cookies="cookies_tao.json"):
    if os.path.exists(os.path.join(os.getcwd(), cookies)):  # 如果不是第一次登陆，则使用cookie登陆
        print("自动登录")
        driver.get(url)
        # 删除第一次登录是储存到本地的cookie
        driver.delete_all_cookies()
        # 读取登录时储存到本地的cookie
        with open(cookies, "r", encoding="utf8") as f:
            list_cookies = json.loads(f.read())

        for cookie in list_cookies:
            driver.add_cookie({
                'domain': cookie['domain'],
                'name': cookie['name'],
                'value': cookie['value'],
                'path': cookie['path'],
                'expires': None
            })
        driver.get(url)
        time.sleep(3)
    else:  # 如果第一次登陆，则手动登陆
        print("请手动登陆")
        driver.get(url)
        driver.find_element_by_class_name("h").click()
        # 手动扫码登录
        inputs = input("请输入一个a：")
        if inputs == "a":
            dict_cookies = driver.get_cookies()
            json_cookies = json.dumps(dict_cookies)
            # 登录完成后,将cookies保存到本地文件
            with open(cookies, "w") as fp:
                fp.write(json_cookies)
            # 跳转新的页面
            handles = driver.window_handles
            print(handles)
            driver.switch_to.window(handles[0])


def get_page(driver, p):
    page = driver.find_element_by_xpath("//*[@id='mainsrp-pager']/div/div/div/div[2]/input")
    page.clear()
    page.send_keys(p)
    time.sleep(1)
    driver.find_element_by_css_selector("#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit").click()


def get_goods_infos(driver, keys):
    """
    获取商品详情信息
    :param driver:
    :param keys:
    :return:
    """
    input = driver.find_element_by_id("q")
    # 1. 搜索关键字
    input.send_keys(keys)
    time.sleep(1)
    driver.find_element_by_xpath('//*[@id="J_TSearchForm"]/div[1]/button').click()
    # 2. 销量从高到低
    time.sleep(1)
    driver.find_element_by_xpath("//*[@id='J_relative']/div[1]/div/ul/li[2]/a").click()
    # 3. 滑动滚动条
    swipe_down(driver, 2)
    # 4. 读取源代码
    page_source = driver.page_source
    # 5. 获取详情信息
    details = get_details(page_source=page_source)

    return details


def get_details(page_source):
    """
    获取结果列表[商品url, 商品名称, 商品图片, 商品价格, 商品成交量, 店铺名称, 店铺地点]
    :param page_source:
    :return:
    """
    soup = BeautifulSoup(page_source, "lxml")

    target_list = soup.find_all("a", class_="pic-link J_ClickStat J_ItemPicA")
    goods_urls = [target.get("href") for target in target_list]  # 商品url
    goods_names = [target.img.get('alt') for target in target_list]  # 商品名称
    goods_pics = ["https:" + target.img.get('data-src', "000") for target in target_list]  # 商品图片
    images_dir = os.path.join(os.getcwd(), "..", "sources", "images")
    try:  # 保存商品图片
        append_str = 0
        for pic, name in zip(goods_pics, goods_names):
            if os.path.exists(name):
                name += str(append_str)
                append_str += 1
                print("保存图片：{}".format(name + ".png"))
                request.urlretrieve(pic,images_dir + os.sep + name + ".png")
            else:
                print("保存图片：{}".format(name + ".png"))
                request.urlretrieve(pic, images_dir + os.sep + name + ".png")
    except FileNotFoundError as e:
        print(e, "保存文件出错")
    except Exception as e:
        print(e)

    try:
        target_list = soup.find_all("div", class_="price g_price g_price-highlight")
        goods_prices = [target.text.strip()[1:] for target in target_list]  # 商品价格
    except:
        print("没有获取到该页面的价格")
        goods_prices = []
    try:
        target_list = soup.find_all("div", class_="deal-cnt")
        goods_deal_vols = [re.search(r'(\d+)', target.text, re.S).group(1) for target in target_list]  # 商品成交量
    except:
        print("没有获取到该页面的成交量")
        goods_deal_vols = []
    try:
        target_list = soup.find_all("a", class_="shopname J_MouseEneterLeave J_ShopInfo")
        shop_names = [target.text.strip() for target in target_list]  # 店铺名称
    except:
        print("没有获取到该页面的店铺名称")
        shop_names = []
    try:
        target_list = soup.find_all("div", class_="item J_MouserOnverReq")
        shop_locations = [target.findNext("div", class_="location").text for target in target_list]  # 店铺地点
    except:
        print("没有获取到该页面的店铺地点")
        shop_locations = []

    for goods_url, goods_name, goods_price, goods_deal_vol, shop_name, shop_location in \
            zip_longest(goods_urls, goods_names, goods_prices, goods_deal_vols, shop_names, shop_locations):
        yield {"goods_url": goods_url, "goods_name": goods_name, "goods_price": goods_price,
                "goods_deal_vol": goods_deal_vol, "shop_name": shop_name, "shop_location": shop_location}


def swipe_down(driver, second):
    for i in range(int(second / 0.1)):
        js = "var q=document.documentElement.scrollTop=" + str(300 + 200 * i)
        driver.execute_script(js)
        time.sleep(0.1)
    js = "var q=document.documentElement.scrollTop=100000"
    driver.execute_script(js)
    time.sleep(0.2)


def main():
    driver = webdriver.Chrome()
    url = "http:www.taobao.com"
    keys = "电脑"
    # 1. 登录
    login(driver, url)
    # 2. 获取详情索引页源代码
    page_source = get_goods_infos(driver, keys)
    # 3. 解析源代码，获取详情url
    details = get_details(page_source)
    print(details)
    # 4. 插入mongodb
    # save_to_mongo(collection, goods_url_list)
    get_page(driver, 3)


if __name__ == "__main__":
    main()
