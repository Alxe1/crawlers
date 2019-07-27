# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : test.py
# @Software: PyCharm
# Desc     :
import os
import random
import time

from bs4 import BeautifulSoup
from taobao.costume.crawler.get_details_url import get_details


f = open(os.path.join(os.getcwd(), "..", "sources", "source.html"), 'r', encoding="utf-8")
page_source = f.read()
f.close()
soup = BeautifulSoup(page_source, "lxml")
target_list = soup.find_all("a", class_="pic-link J_ClickStat J_ItemPicA")
goods_pics = [target.img.get('data-src', "000") for target in target_list]
print(goods_pics)






