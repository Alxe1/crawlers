# -*- coding: utf-8 -*-
# @Author  : LiuLei
# @File    : get_similar_goods.py
# @Software: PyCharm
# @Time    : 2019/7/27 14:17
# Desc     :

import os
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC