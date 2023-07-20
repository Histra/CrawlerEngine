# -*- coding: utf-8 -*-
# @Time    : 2023/7/20 19:40
# @Author  : Histranger
# @File    : test_chrome_crawler.py
# @Software: PyCharm
"""
References:
    https://docs.python.org/zh-cn/3/library/unittest.html
"""

import unittest

from selenium.webdriver.common.by import By

from chrome_crawler import ChromeCrawler


class ChromeCrawlerTestCase(unittest.TestCase):
    url = 'https://docs.python.org/zh-cn/3/library/unittest.html'
    url_err = f"{url}foobar"

    def setUp(self) -> None:
        self.cc = ChromeCrawler(driver_path='./chromedriver/v116/chromedriver.exe')

    def tearDown(self) -> None:
        self.cc.close()

    def test_try_get_1(self):
        ok, msg = self.cc.try_get(url=self.url)
        self.assertTrue(ok, msg)
        self.assertTrue(msg == f"get url[{self.url}] OK.", msg)

    def test_try_get_2(self):
        ok, msg = self.cc.try_get(url=self.url_err, err_msg='404 Not Found')
        self.assertFalse(ok, msg)
        self.assertTrue(msg == f"err_msg[404 Not Found] in page source.", msg)

    def test_try_get_3(self):
        ok, msg = self.cc.try_get(url=self.url_err, key_msg='404 Not Found')
        self.assertTrue(ok, msg)
        self.assertTrue('nginx' in self.cc.driver.page_source, msg)

    def test_try_get_4(self):
        self.cc.try_get(self.url)
        otc_ele = self.cc.driver.find_element(By.CSS_SELECTOR, '#organizing-test-code > h2')
        self.assertTrue(otc_ele.text.strip() == '组织你的测试代码', otc_ele.text.strip())
