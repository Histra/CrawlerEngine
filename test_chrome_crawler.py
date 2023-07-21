# -*- coding: utf-8 -*-
# @Time    : 2023/7/20 19:40
# @Author  : Histranger
# @File    : test_chrome_crawler.py
# @Software: PyCharm
"""
References:
    https://docs.python.org/zh-cn/3/library/unittest.html
"""
import logging
import random
import re
import time
import unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from chrome_crawler import ChromeCrawler
from captcha_solver import get_solver

logging.basicConfig(level=logging.INFO)


class ChromeCrawlerTestCase(unittest.TestCase):
    url = 'https://docs.python.org/zh-cn/3/library/unittest.html'
    url_err = f"{url}foobar"

    cloudflare_block_url: str = 'https://nowsecure.nl'

    def setUp(self) -> None:
        self.cc = ChromeCrawler(headless=False, driver_path='./chromedriver/v116/chromedriver.exe')

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

    def test_get_cloudflare_block_1(self):
        ok, msg = self.cc.try_get(self.cloudflare_block_url)
        self.assertTrue(ok, msg)
        cloudflare_elem = self.cc.driver.find_element(By.CSS_SELECTOR, '#footer-text > a')
        self.assertTrue(cloudflare_elem.text.strip() == 'Cloudflare')

    def test_bypass_cloudflare_block_1(self):
        """
        Opps, can not bypass cloudflare. :(
        """

        ok, msg = self.cc.try_get(self.cloudflare_block_url)
        self.assertTrue(ok, msg)

        try:
            cf_iframe = WebDriverWait(self.cc.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[id]'))
            )
        except Exception as e:
            raise e
        else:
            self.cc.driver.switch_to.frame(cf_iframe)

        try:
            cloudflare_elem = WebDriverWait(self.cc.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=checkbox]"))
            )
        except Exception as e:
            raise e
        else:
            cloudflare_elem.click()

        self.cc.driver.switch_to.default_content()
        time.sleep(60)

        time.sleep(random.uniform(1, 3))

        try:
            element = WebDriverWait(self.cc.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'main h1'))
            )
        except Exception as e:
            raise e
        else:
            self.assertTrue(element and element.text.strip() == 'OH YEAH, you passed!',
                            f"ERR: element = {repr(element)}")

    def test_bypass_cloudflare_block_with_2captcha(self):
        """
        Opps, some error occurred, will fix in the future. :(
        If you want to bypass Cloudflare, please use uc_crawler.py, manual or auto.
        """
        ok, msg = self.cc.try_get(self.cloudflare_block_url)
        self.assertTrue(ok, msg)

        cf_iframe = WebDriverWait(self.cc.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe[id]'))
        )
        self.cc.driver.switch_to.frame(cf_iframe)

        cloudflare_elem = WebDriverWait(self.cc.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type=checkbox]"))
        )
        time.sleep(random.uniform(1, 3))

        site_key = re.findall(r"chlApiSitekey: '(.*?)',", self.cc.driver.page_source)
        self.assertTrue(site_key, f"can not get site-key. | {self.cc.driver.page_source}")
        site_key = site_key[0].strip()
        logging.info(f"site-key = {site_key}")

        self.cc.driver.switch_to.default_content()

        solver = get_solver("Cloudflare")
        code = solver.solve(site_key=site_key, url=self.cc.driver.current_url)
        self.assertIsNotNone(code, "get code failed.")

    def test_bypass_cloudflare_block_with_manual(self):
        """
        Opps, also failed. :(
        """
        ok, msg = self.cc.try_get(self.cloudflare_block_url)
        self.assertTrue(ok, msg)

        logging.warning("Please bypass captcha as soon as you can. [must in 30s]")

        try:
            element = WebDriverWait(self.cc.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'main h1'))
            )
        except Exception as e:
            raise e
        else:
            self.assertTrue(element and element.text.strip() == 'OH YEAH, you passed!',
                            f"ERR: element = {repr(element)}")








