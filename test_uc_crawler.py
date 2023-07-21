# -*- coding: utf-8 -*-
# @Time    : 2023/7/20 14:54
# @Author  : Histranger
# @File    : test_uc_crawler.py
# @Software: PyCharm
import logging
import unittest

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from uc_crawler import UCCrawler

logging.basicConfig(level=logging.INFO)


class UCCrawlerTestCase(unittest.TestCase):
    cloudflare_block_url: str = 'https://nowsecure.nl'

    def setUp(self) -> None:
        self.ucc = UCCrawler(headless=False)

    def tearDown(self) -> None:
        self.ucc.close()

    def test_bypass_cloudflare_block_with_manual(self):
        ok, msg = self.ucc.try_get(self.cloudflare_block_url)
        self.assertTrue(ok, msg)

        logging.warning("Please bypass captcha as soon as you can. [must in 30s]")

        try:
            element = WebDriverWait(self.ucc.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'main h1'))
            )
        except Exception as e:
            raise e
        else:
            self.assertTrue(element and element.text.strip() == 'OH YEAH, you passed!',
                            f"ERR: element = {repr(element)}")
